#!/usr/bin/env python3
"""DeepBattler -- Claude Code (CLI) caller.

Drive DeepBattler with your **Claude Max subscription** instead of a paid API
key. This script shells out to the local ``claude`` CLI (Claude Code) in
headless / print mode (``claude -p``), so every request uses your logged-in
subscription -- no ANTHROPIC_API_KEY and no per-token billing.

Modes
-----
``--mode battlegrounds`` (default): Hearthstone Battlegrounds coach. Reads the
    Battlegrounds state the original HDT plugin writes.
``--mode standard`` (experimental): Standard / constructed ladder coach. Reads
    the constructed state the Standard plugin writes
    (``real_time_caller/latest_standard_state.json``) and uses
    ``util/Prompt_standard.txt``. Heads up: an LLM is only an OK constructed
    player -- weak at exact lethal math and stale on new-set meta -- so treat
    this as an assistant, not an autopilot.

What it does
------------
1. Watches the game-state JSON the HDT plugin writes.
2. On every meaningful change, asks Claude for one concise recommendation for
   the current decision.
3. Writes the advice to ``real_time_caller/agent_output.txt`` -- the in-game
   overlay window (AgentOutputWindow) reads exactly this file -- and prints it.
4. Optionally speaks the advice aloud with offline TTS (``--tts``, needs
   ``pip install pyttsx3``). Claude has no native voice API, so this is local.

Persistent conversation (default)
---------------------------------
By default the script keeps ONE Claude conversation alive for the whole game
via ``--session-id`` / ``--resume``: the strategy guide is sent only on the
first turn, and every later turn sends just the new game state. Claude remembers
the earlier turns and its own prior advice, so you never re-explain the rules.
A new conversation starts automatically when a new game begins (turn counter
resets). Use ``--no-session`` to make every call independent instead.

First-time setup
----------------
Install Claude Code and log in with your Max account once::

    claude            # then run /login and pick "Claude account (subscription)"

Then run::

    python claude_caller.py                       # Battlegrounds, model sonnet
    python claude_caller.py --mode standard        # Standard ladder (experimental)
    python claude_caller.py --mode standard --model opus --tts
    python claude_caller.py --mode standard --once  # one-shot test on current state

No API key required. If ANTHROPIC_API_KEY happens to be set in your environment
it is stripped from the child process so calls still use your subscription.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

# --- File roots --------------------------------------------------------------
# Prompt files are repo assets -> resolved relative to this script.
# Runtime game IO must match the C# plugin, which writes to %Desktop%\DeepBattler\Agent
# by default or to DEEPBATTLER_AGENT_DIR if set.
REAL_TIME_CALLER_DIR = Path(__file__).resolve().parent
BASE_DIR = REAL_TIME_CALLER_DIR.parent  # the repo's Agent/ directory

_io_root_env = os.environ.get("DEEPBATTLER_AGENT_DIR")
IO_ROOT = Path(_io_root_env) if _io_root_env else BASE_DIR

AGENT_OUTPUT_FILE = IO_ROOT / "real_time_caller" / "agent_output.txt"
META_DIR = BASE_DIR / "meta"  # per-class meta notes (repo asset, read live each game)

DEFAULT_MODEL = os.environ.get("DEEPBATTLER_MODEL", "sonnet")

# --- Per-mode persona + instruction (system-prompt channel stays short) ------
PERSONA = {
    "battlegrounds": (
        "You are DeepBattler, a witty top-0.1% Hearthstone Battlegrounds coach. "
        "Reply with ONE recommendation for the current turn in 1-2 short, concrete "
        "sentences (reference the actual minions and gold). A light pun is fine. "
        "No preamble, no markdown headers."
    ),
    "standard": (
        "You are DeepBattler, a real-time Hearthstone constructed analysis co-pilot. "
        "Think ALONGSIDE the player: surface the key reads and considerations for the "
        "current decision (opponent's likely deck, tempo/race, trades, draws/outs, "
        "hand-reads, lethal both ways) as a concise, scannable analysis -- a one-line "
        "read, then 2-4 relevant bullets, then any lethal/danger flag. Perspective and "
        "options, not one barked move. Be honest about hidden info ('likely', not "
        "certain). Trust the provided LETHAL/THREAT math."
    ),
}
INSTRUCTION = {
    "battlegrounds": (
        "Based on the current Hearthstone Battlegrounds game state below -- and our "
        "earlier turns this game, if any -- give your single best move for THIS turn "
        "(buy / sell / roll / upgrade / position) in 1-2 short, concrete sentences "
        "referencing the actual minions and gold."
    ),
    "standard": (
        "Analyze the current Hearthstone (Standard) game state below. Give a concise, "
        "scannable real-time read for THIS decision: lead with who's ahead / who's "
        "faster and the key question, then the 2-4 most relevant considerations (trades, "
        "what to play around, hand-reads, draws/outs), then flag lethal or incoming "
        "lethal using the LETHAL/THREAT checks. Cover what matters NOW, not every angle. "
        "Honest probabilistic reads for hidden info; trust the provided lethal/threat numbers."
    ),
}


def log(msg: str) -> None:
    print(msg, flush=True)


def resolve_paths(mode: str):
    """Return (latest_state, fallback_state, prompt_file) for the mode."""
    rt = IO_ROOT / "real_time_caller"
    if mode == "standard":
        return (
            rt / "latest_standard_state.json",
            IO_ROOT / "standard_game_state.json",
            BASE_DIR / "util" / "Prompt_standard.txt",
        )
    return (
        rt / "latest_game_state.json",
        IO_ROOT / "game_state.json",
        BASE_DIR / "util" / "Prompt.txt",
    )


def find_claude(explicit: str | None = None) -> str | None:
    """Locate the claude executable (respects PATHEXT so it finds claude.cmd)."""
    candidate = explicit or os.environ.get("DEEPBATTLER_CLAUDE_BIN") or "claude"
    resolved = shutil.which(candidate)
    if resolved:
        return resolved
    p = Path(candidate)
    return str(p) if p.is_file() else None


def build_cmd(claude_bin: str, args: list[str]) -> list[str]:
    """Wrap .cmd/.bat shims through cmd.exe (Windows can't exec them directly)."""
    if os.name == "nt" and str(claude_bin).lower().endswith((".cmd", ".bat")):
        return ["cmd", "/c", claude_bin, *args]
    return [claude_bin, *args]


def load_guide(prompt_file: Path) -> str:
    try:
        if prompt_file.exists():
            text = prompt_file.read_text(encoding="utf-8").strip()
            if text:
                return text
    except Exception as e:  # noqa: BLE001 - never crash on prompt loading
        log(f"[WARN] Could not read {prompt_file.name}: {e}")
    return ""


def pick_state_file(latest: Path, fallback: Path, override: str | None) -> Path:
    if override:
        return Path(override)
    if latest.exists():
        return latest
    return fallback


def load_game_state(path: Path) -> dict | None:
    """Read and validate the game-state JSON. Returns None if not ready."""
    try:
        if not path.exists():
            return None
        # utf-8-sig tolerates a BOM if the C# side ever writes one.
        content = path.read_text(encoding="utf-8-sig").strip()
        if not content or content == "{}":
            return None
        data = json.loads(content)
        if isinstance(data, dict) and "game_state" in data:
            return data
    except json.JSONDecodeError:
        # File is probably mid-write; try again next tick.
        return None
    except Exception as e:  # noqa: BLE001
        log(f"[WARN] Could not read state file: {e}")
    return None


def turn_of(state: dict) -> int:
    try:
        return int(state.get("game_state", {}).get("turn_number", 0))
    except (TypeError, ValueError):
        return 0


def _board_str(board) -> str:
    if not board:
        return "empty"
    out = []
    for m in board:
        s = f"{m.get('name', '?')} {m.get('attack', '?')}/{m.get('health', '?')}"
        kw = "".join(
            tag for flag, tag in (("taunt", "T"), ("divine_shield", "D"),
                                   ("stealth", "S"), ("poisonous", "P"),
                                   ("frozen", "F")) if m.get(flag)
        )
        if kw:
            s += f"[{kw}]"
        out.append(s)
    return ", ".join(out)


def summarize_standard(state: dict) -> str:
    gs = state.get("game_state", {})
    me = state.get("player", {})
    opp = state.get("opponent", {})

    def hand_str(h):
        return ", ".join(f"{c.get('name', '?')}({c.get('cost', '?')})" for c in h) if h else "empty"

    played = ", ".join(c.get("name", "?") for c in opp.get("known_played_cards", [])) or "none"
    me_hero = me.get("hero") or me.get("class") or "?"
    opp_hero = opp.get("hero") or opp.get("class") or "?"
    return "\n".join(
        [
            f"Turn {gs.get('turn_number', '?')} | {gs.get('phase', '?')} | active: {gs.get('active_player', '?')}",
            f"YOU ({me_hero}): {me.get('health', '?')}+{me.get('armor', 0)} HP "
            f"| mana {me.get('mana_available', '?')}/{me.get('mana_total', '?')}",
            f"  hand: {hand_str(me.get('hand', []))}",
            f"  board: {_board_str(me.get('board', []))}",
            f"OPP ({opp_hero}): {opp.get('health', '?')}+{opp.get('armor', 0)} HP "
            f"| hand {opp.get('hand_count', '?')} cards | secrets {opp.get('secrets_count', 0)}",
            f"  board: {_board_str(opp.get('board', []))}",
            f"  played so far: {played}",
        ]
    )


def summarize_battlegrounds(state: dict) -> str:
    gs = state.get("game_state", {})
    hero = state.get("player_hero", {})
    res = state.get("resources", {})
    board = state.get("board_state", {})
    return "\n".join(
        [
            f"Turn {gs.get('turn_number', '?')} | Phase {gs.get('phase', '?')}",
            f"Hero {hero.get('name', '?')} | HP {hero.get('current_health', '?')}",
            f"Gold {res.get('available_gold', '?')} | Tier {res.get('tavern_tier', '?')} "
            f"| Upgrade {res.get('tavern_upgrade_cost', '?')}",
            f"Board {board.get('warband_size', 0)}/7 | Tavern offers "
            f"{board.get('tavern_available', 0)} | Hand {board.get('hand_size', 0)}",
        ]
    )


def summarize(state: dict) -> str:
    # Detect schema so the summary is right even if --mode is mismatched.
    if "opponent" in state or "player" in state:
        return summarize_standard(state)
    return summarize_battlegrounds(state)


# ---------------------------------------------------------------------------
# Standard-mode helpers: deterministic lethal math + per-class meta notes.
# These offload the LLM's two weak spots (exact arithmetic, stale meta).
# ---------------------------------------------------------------------------

HERO_TO_CLASS = {
    "jaina proudmoore": "mage", "rexxar": "hunter", "uther lightbringer": "paladin",
    "thrall": "shaman", "gul'dan": "warlock", "garrosh hellscream": "warrior",
    "malfurion stormrage": "druid", "anduin wrynn": "priest",
    "valeera sanguinar": "rogue", "illidan stormrage": "demonhunter",
}
_DEAL_RE = re.compile(r"[Dd]eal[s]?\s+\$?(\d+)\s+damage")
_ATK_BUFF_RE = re.compile(r"\+\d+\s*Attack|gain[s]?\s+\+?\d*\s*Attack|give[s]?\b.*\bAttack", re.IGNORECASE)


def _ready_attackers(board):
    out = []
    for m in board or []:
        ready = m.get("ready")
        if ready is None:  # older state without the field: best-effort
            ready = (m.get("attack", 0) or 0) > 0 and not m.get("frozen")
        if ready and (m.get("attack", 0) or 0) > 0:
            out.append(m)
    return out


def compute_lethal(state):
    """Best-effort lethal helper for Standard.

    It computes ONLY the reliable, deterministic part (ready board attack +
    windfury + weapon vs the opponent's effective HP, plus flat 'Deal N damage'
    burn in hand) and then explicitly LISTS the complications it can NOT resolve
    (divine shield, taunt clearing, your own attack buffs / board growth, hero
    power, location / random / conditional effects) so Claude factors them in.
    It is a grounded checklist, not a full combat simulator. Returns text or None.
    """
    me = state.get("player")
    opp = state.get("opponent")
    if not me or not opp:
        return None

    attackers = _ready_attackers(me.get("board", []))
    board_dmg = sum((m.get("attack", 0) or 0) * (2 if m.get("windfury") else 1) for m in attackers)
    weapon = me.get("weapon")
    hero_can = me.get("hero_can_attack")
    weapon_dmg = (weapon.get("attack", 0) or 0) if (weapon and (hero_can is None or hero_can)) else 0
    raw = board_dmg + weapon_dmg
    opp_hp = (opp.get("health", 0) or 0) + (opp.get("armor", 0) or 0)
    opp_board = opp.get("board", [])
    taunts = [m for m in opp_board if m.get("taunt")]

    burns = []
    for c in me.get("hand", []):
        mt = _DEAL_RE.search(c.get("description", "") or "")
        if mt:
            burns.append((c.get("name", "?"), int(mt.group(1))))
    burn_total = sum(d for _, d in burns)

    lines = ["⚔️ LETHAL CHECK — reliable arithmetic only (complications listed after):"]
    atk_list = ", ".join(
        f"{m.get('name', '?')} {m.get('attack', 0)}" + ("x2(WF)" if m.get("windfury") else "")
        for m in attackers
    ) or "none"
    lines.append(f"  - Ready attackers: {atk_list} = {board_dmg} board dmg")
    if weapon_dmg:
        lines.append(f"  - Weapon: {weapon.get('name', '?')} {weapon_dmg}")
    lines.append(f"  - Raw face damage (taunts ignored): {raw}")
    lines.append(f"  - Opponent effective HP: {opp_hp} (health {opp.get('health', '?')} + armor {opp.get('armor', 0)})")
    if burns:
        lines.append(
            "  - Flat burn in hand ('Deal N damage'): "
            + ", ".join(f"{n} {d}" for n, d in burns)
            + f" = up to {burn_total} (only if face-targetable)"
        )

    # Complications NOT included in the number above — surface them, don't fake them.
    comp = []
    if taunts:
        comp.append(
            "Opponent TAUNTS (clear before any face): "
            + ", ".join(
                f"{m.get('name', '?')} {m.get('attack', 0)}/{m.get('health', '?')}"
                + (" [Divine Shield → needs an extra hit to pop]" if m.get("divine_shield") else "")
                for m in taunts
            )
        )
    ds_nontaunt = [m for m in opp_board if m.get("divine_shield") and not m.get("taunt")]
    if ds_nontaunt:
        comp.append("Opponent Divine Shields (each eats one hit): " + ", ".join(m.get("name", "?") for m in ds_nontaunt))
    my_poison = [m for m in attackers if m.get("poisonous")]
    if my_poison and taunts:
        comp.append("Your Poisonous attackers can kill any ONE taunt cheaply: " + ", ".join(m.get("name", "?") for m in my_poison))
    buff_cards = [c.get("name", "?") for c in me.get("hand", []) if _ATK_BUFF_RE.search(c.get("description", "") or "")]
    if buff_cards:
        comp.append("Attack buffs in HAND (extra dmg if played; sequence first): " + ", ".join(buff_cards))
    growth = [
        m.get("name", "?") for m in me.get("board", [])
        if "attack" in (m.get("description", "") or "").lower()
        and ("gain" in (m.get("description", "") or "").lower() or "+" in (m.get("description", "") or ""))
    ]
    if growth:
        comp.append("Your minions that GROW attack on a trigger (e.g. on spell cast): " + ", ".join(growth))

    lines.append("  - NOT counted above — you must factor these in yourself:")
    for c in comp:
        lines.append(f"      • {c}")
    lines.append("      • Hero-power damage, location cards, and random/conditional effects are NOT computed.")

    # Verdict from the reliable numbers only, honestly caveated.
    if taunts:
        verdict = "Taunts in the way — clear them (mind Divine Shield), then re-check face damage."
    elif raw >= opp_hp:
        verdict = f"LETHAL on board alone ({raw} >= {opp_hp})."
    elif raw + burn_total >= opp_hp:
        verdict = f"POSSIBLE lethal with burn ({raw}+{burn_total} >= {opp_hp}) — verify targets/mana/Divine Shield."
    else:
        verdict = f"NOT lethal by board+flat burn ({raw}+{burn_total} < {opp_hp}); buffs/hero-power/locations above could still close it."
    lines.append(f"  - Verdict (reliable numbers only): {verdict}")
    return "\n".join(lines)


def compute_threat(state):
    """Best-effort 'am I about to be killed?' check for Standard: the opponent's
    board + weapon attack vs your effective HP. Hidden hand burst is NOT counted
    (it is hidden) -- treat this as a FLOOR on incoming damage. Returns text or None."""
    me = state.get("player")
    opp = state.get("opponent")
    if not me or not opp:
        return None
    opp_board = opp.get("board", [])
    board_atk = sum(
        (m.get("attack", 0) or 0) * (2 if m.get("windfury") else 1)
        for m in opp_board if (m.get("attack", 0) or 0) > 0
    )
    weapon = opp.get("weapon")
    wpn = (weapon.get("attack", 0) or 0) if weapon else 0
    incoming = board_atk + wpn
    my_hp = (me.get("health", 0) or 0) + (me.get("armor", 0) or 0)
    my_taunts = [m for m in me.get("board", []) if m.get("taunt")]

    lines = ["🛡 THREAT CHECK — opponent board+weapon damage to you (hidden hand burst NOT counted; this is a floor):"]
    lines.append(f"  - Opponent board+weapon attack: {incoming}")
    lines.append(f"  - Your effective HP: {my_hp} (health {me.get('health', '?')} + armor {me.get('armor', 0)})")
    if my_taunts:
        lines.append(
            "  - Your taunts (they must come through these first): "
            + ", ".join(f"{m.get('name', '?')} {m.get('attack', 0)}/{m.get('health', '?')}" for m in my_taunts)
        )
    if incoming >= my_hp and not my_taunts:
        lines.append(f"  - ⚠ You could DIE to their board alone next turn ({incoming} >= {my_hp}) -- stabilize (taunt/heal/armor/clear).")
    elif incoming >= my_hp - 10:
        lines.append("  - You're within burst range -- account for hidden burn/charge from hand before tapping out.")
    return "\n".join(lines)


def _opponent_class(state):
    opp = state.get("opponent", {})
    cls = (opp.get("class") or "").strip().lower()
    if cls and cls not in ("invalid", "neutral"):
        return cls
    return HERO_TO_CLASS.get((opp.get("hero") or "").strip().lower(), "")


def load_meta(state):
    """Read general.md + the opponent class's meta file (live, no rebuild needed)."""
    if not META_DIR.exists():
        return ""
    parts = []
    for path in (META_DIR / "general.md", META_DIR / f"{_opponent_class(state)}.md"):
        if path.exists():
            try:
                t = path.read_text(encoding="utf-8").strip()
                if t:
                    parts.append(t)
            except Exception:  # noqa: BLE001
                pass
    body = "\n\n".join(parts)
    return ("=== META NOTES (current ladder; refresh per patch) ===\n" + body) if body else ""


def build_stdin(state: dict, guide: str, meta: str = "", tactical: str = "") -> str:
    """guide/meta are included only on the first turn; tactical (lethal+threat) every turn."""
    parts = []
    if guide:
        parts.append("=== DEEPBATTLER STRATEGY GUIDE ===\n" + guide)
    if meta:
        parts.append(meta)
    parts.append("=== CURRENT GAME STATE (summary) ===\n" + summarize(state))
    parts.append(
        "=== CURRENT GAME STATE (full JSON) ===\n"
        + json.dumps(state, indent=2, ensure_ascii=False)
    )
    if tactical:
        parts.append(tactical)
    return "\n\n".join(parts) + "\n"


def run_claude(claude_bin, model, instruction, persona, stdin_data, timeout,
               session_id=None, is_first=True):
    """Run one headless claude call. Returns (advice, error).

    session_id=None  -> independent one-off call (persona + guide each time).
    is_first=True    -> create the session (--session-id) and set the persona.
    is_first=False   -> resume the existing conversation (--resume); the guide
                        already lives in history, so don't resend it.
    """
    env = os.environ.copy()
    # Force the Max *subscription* (OAuth). A stray API key would override it and
    # bill per token instead of using the subscription.
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)

    inner = ["-p", instruction, "--model", model, "--output-format", "text"]
    if session_id is None:
        inner += ["--append-system-prompt", persona]
    elif is_first:
        inner += ["--session-id", session_id, "--append-system-prompt", persona]
    else:
        inner += ["--resume", session_id]

    cmd = build_cmd(claude_bin, inner)
    try:
        proc = subprocess.run(
            cmd,
            input=stdin_data,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, f"claude timed out after {timeout:g}s"
    except FileNotFoundError:
        return None, f"could not launch '{claude_bin}'"
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        return None, err or f"claude exited with code {proc.returncode}"
    return (proc.stdout or "").strip(), None


def write_output(text: str) -> None:
    try:
        AGENT_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        AGENT_OUTPUT_FILE.write_text(text, encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        log(f"[WARN] Could not write {AGENT_OUTPUT_FILE.name}: {e}")


def make_speaker(enabled: bool):
    if not enabled:
        return lambda _t: None
    try:
        import pyttsx3  # type: ignore

        engine = pyttsx3.init()
    except Exception:  # noqa: BLE001
        log("[WARN] --tts requested but pyttsx3 is unavailable. Install: pip install pyttsx3")
        return lambda _t: None

    def speak(text: str) -> None:
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:  # noqa: BLE001
            log(f"[WARN] TTS failed: {e}")

    return speak


def process_state(claude_bin, model, cfg, state, speak, timeout, session_id, is_first):
    turn = turn_of(state)
    write_output(f"\U0001f914 Analyzing turn {turn}...")
    include_guide = (session_id is None) or is_first
    is_standard = cfg.get("mode") == "standard"
    meta = load_meta(state) if (is_standard and include_guide) else ""
    tactical = ""
    if is_standard:
        tactical = "\n\n".join(t for t in (compute_lethal(state), compute_threat(state)) if t)
    stdin_data = build_stdin(state, cfg["guide"] if include_guide else "", meta, tactical)
    advice, err = run_claude(
        claude_bin, model, cfg["instruction"], cfg["persona"], stdin_data, timeout,
        session_id=session_id, is_first=is_first,
    )
    if err:
        log(f"[ERROR] {err}")
        write_output("⚠️ Claude call failed -- check the console.")
        return
    if not advice:
        log("[WARN] Empty response from Claude.")
        return
    log(f"\n\U0001f4a1 {advice}\n")
    write_output(advice)
    speak(advice)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DeepBattler -- drive the coach with your Claude Max subscription "
        "via the local claude CLI (no API key)."
    )
    parser.add_argument("--mode", choices=["battlegrounds", "standard"],
                        default="battlegrounds",
                        help="battlegrounds (default) or standard (experimental ladder coach)")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help="claude model alias: sonnet | opus | haiku | fable "
                             "(default: %(default)s; env DEEPBATTLER_MODEL)")
    parser.add_argument("--no-session", action="store_true",
                        help="make every call independent instead of continuing one "
                             "conversation per game (re-sends the strategy guide each turn)")
    parser.add_argument("--tts", action="store_true",
                        help="speak advice aloud via offline pyttsx3")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="seconds between state-file checks (default: %(default)s)")
    parser.add_argument("--cooldown", type=float, default=2.0,
                        help="min seconds between Claude calls, to spare subscription "
                             "usage (default: %(default)s)")
    parser.add_argument("--timeout", type=float, default=90.0,
                        help="seconds before a single Claude call is abandoned "
                             "(default: %(default)s)")
    parser.add_argument("--prompt-file", default=None,
                        help="override the strategy prompt file")
    parser.add_argument("--state-file", default=None,
                        help="override the game-state JSON path to watch")
    parser.add_argument("--claude-bin", default=None,
                        help="path to the claude executable (env DEEPBATTLER_CLAUDE_BIN)")
    parser.add_argument("--once", action="store_true",
                        help="evaluate the current state once and exit (handy for testing)")
    args = parser.parse_args()

    claude_bin = find_claude(args.claude_bin)
    if not claude_bin:
        log("[FATAL] Could not find the 'claude' CLI on your PATH.\n"
            "        Install Claude Code, then run `claude` once and /login with your\n"
            "        Claude Max account. Docs: https://docs.claude.com/en/docs/claude-code")
        sys.exit(1)

    latest, fallback, default_prompt = resolve_paths(args.mode)
    prompt_file = Path(args.prompt_file) if args.prompt_file else default_prompt
    cfg = {
        "guide": load_guide(prompt_file),
        "persona": PERSONA[args.mode],
        "instruction": INSTRUCTION[args.mode],
        "mode": args.mode,
    }
    use_session = not args.no_session
    speak = make_speaker(args.tts)

    log("=" * 66)
    log("DeepBattler -- Claude Code caller (using your Claude Max subscription)")
    log(f"  mode:      {args.mode}" + ("  (experimental)" if args.mode == "standard" else ""))
    log(f"  claude:    {claude_bin}")
    log(f"  model:     {args.model}")
    log(f"  guide:     {prompt_file if cfg['guide'] else '(built-in default persona only)'}")
    log(f"  watching:  {pick_state_file(latest, fallback, args.state_file)}")
    log(f"  output ->  {AGENT_OUTPUT_FILE}")
    log(f"  session:   {'continuous per game (remembers prior turns)' if use_session else 'independent calls'}")
    log(f"  TTS:       {'on' if args.tts else 'off (use --tts for voice)'}")
    if os.environ.get("ANTHROPIC_API_KEY"):
        log("  note:      ANTHROPIC_API_KEY is set but will be IGNORED so calls use\n"
            "             your subscription, not per-token API billing.")
    log("=" * 66)

    if args.once:
        state = load_game_state(pick_state_file(latest, fallback, args.state_file))
        if not state:
            log("[INFO] No valid game state available right now.")
            return
        process_state(claude_bin, args.model, cfg, state, speak, args.timeout,
                      session_id=None, is_first=True)
        return

    log("Watching for game-state changes... (Ctrl+C to stop)\n")
    last_mtime = None
    last_hash = None
    last_call = 0.0
    session_id = None
    last_turn = None
    try:
        while True:
            time.sleep(args.interval)
            state_file = pick_state_file(latest, fallback, args.state_file)
            if not state_file.exists():
                continue
            try:
                mtime = state_file.stat().st_mtime
            except OSError:
                continue
            if mtime == last_mtime:
                continue
            last_mtime = mtime

            state = load_game_state(state_file)
            if not state:
                continue

            # Only act on genuinely new states, and not faster than the cooldown.
            state_hash = hash(json.dumps(state, sort_keys=True))
            if state_hash == last_hash:
                continue
            if time.time() - last_call < args.cooldown:
                continue
            last_hash = state_hash
            last_call = time.time()

            turn = turn_of(state)

            # Session lifecycle: start a fresh conversation for a new game
            # (first run, or the turn counter dropped = a new game began).
            is_first = False
            if use_session:
                if session_id is None or (last_turn is not None and turn < last_turn):
                    session_id = str(uuid.uuid4())
                    is_first = True
            active_session = session_id if use_session else None
            last_turn = turn

            phase = state.get("game_state", {}).get("phase", "?")
            tag = "new game" if is_first else ("resume" if use_session else "independent")
            log(f"[turn {turn} | {phase} | {tag}] state changed -> asking Claude ({args.model})...")
            process_state(claude_bin, args.model, cfg, state, speak, args.timeout,
                          session_id=active_session, is_first=is_first)
    except KeyboardInterrupt:
        log("\nBye! \U0001f37b")


if __name__ == "__main__":
    main()
