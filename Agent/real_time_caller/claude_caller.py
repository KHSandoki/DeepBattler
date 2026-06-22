#!/usr/bin/env python3
"""DeepBattler -- Claude Code (CLI) caller.

Drive DeepBattler with your **Claude Max subscription** instead of a paid API
key. This script shells out to the local ``claude`` CLI (Claude Code) in
headless / print mode (``claude -p``), so every request uses your logged-in
subscription -- no ANTHROPIC_API_KEY and no per-token billing.

What it does
------------
1. Watches the game-state JSON the HDT plugin writes
   (``real_time_caller/latest_game_state.json``, falling back to
   ``game_state.json``).
2. On every meaningful change, asks Claude for one concise Battlegrounds
   recommendation for the current turn.
3. Writes the advice to ``real_time_caller/agent_output.txt`` -- the in-game
   overlay window (AgentOutputWindow) reads exactly this file -- and prints it
   to the console.
4. Optionally speaks the advice aloud with offline TTS (``--tts``, needs
   ``pip install pyttsx3``). Claude has no native voice API, so this is local.

Persistent conversation (default)
---------------------------------
By default the script keeps ONE Claude conversation alive for the whole game
via ``--session-id`` / ``--resume``: the strategy guide is sent only on the
first turn, and every later turn sends just the new game state. Claude remembers
the earlier turns and its own prior advice, so you never re-explain the rules
("you upgraded to tier 3 last turn as I suggested; now..."). A new conversation
starts automatically when a new game begins (turn counter resets). Use
``--no-session`` to make every call independent instead.

Note: this is *conversation* persistence (each turn still launches a fresh
``claude`` process that reloads the saved session from disk), not a warm
long-lived process. For turn-based play the ~1-2s startup per turn is fine.

First-time setup
----------------
Install Claude Code and log in with your Max account once::

    claude            # then run /login and pick "Claude account (subscription)"

Then just run::

    python claude_caller.py            # default model: sonnet, session ON
    python claude_caller.py --model opus --tts
    python claude_caller.py --no-session   # independent calls (re-send guide each time)

No API key required. If ANTHROPIC_API_KEY happens to be set in your environment
it is stripped from the child process so calls still use your subscription.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

# --- File paths --------------------------------------------------------------
# Prompt.txt is a repo asset -> always resolved relative to this script.
# Runtime game IO (state in, advice out) must match the C# plugin, which writes
# to %Desktop%\DeepBattler\Agent by default or to DEEPBATTLER_AGENT_DIR if set.
REAL_TIME_CALLER_DIR = Path(__file__).resolve().parent
BASE_DIR = REAL_TIME_CALLER_DIR.parent  # the repo's Agent/ directory

_io_root_env = os.environ.get("DEEPBATTLER_AGENT_DIR")
IO_ROOT = Path(_io_root_env) if _io_root_env else BASE_DIR

PROMPT_FILE = BASE_DIR / "util" / "Prompt.txt"
LATEST_GAME_STATE_FILE = IO_ROOT / "real_time_caller" / "latest_game_state.json"
GAME_STATE_FILE = IO_ROOT / "game_state.json"
AGENT_OUTPUT_FILE = IO_ROOT / "real_time_caller" / "agent_output.txt"

DEFAULT_MODEL = os.environ.get("DEEPBATTLER_MODEL", "sonnet")

# Short persona for the system-prompt channel. Kept tiny so the command line
# stays well under Windows' cmd.exe limit; the full strategy guide (Prompt.txt)
# is sent through stdin instead.
PERSONA = (
    "You are DeepBattler, a witty top-0.1% Hearthstone Battlegrounds coach. "
    "Reply with ONE recommendation for the current turn in 1-2 short, concrete "
    "sentences (reference the actual minions and gold). A light pun is fine. "
    "No preamble, no markdown headers."
)

# The positional prompt. The bulky guide + game state ride on stdin.
INSTRUCTION = (
    "Based on the current Hearthstone Battlegrounds game state below -- and our "
    "earlier turns this game, if any -- give your single best move for THIS turn "
    "(buy / sell / roll / upgrade / position) in 1-2 short, concrete sentences "
    "referencing the actual minions and gold."
)


def log(msg: str) -> None:
    print(msg, flush=True)


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


def load_strategy_guide() -> str:
    """Load Prompt.txt (the strategy knowledge base) if present."""
    try:
        if PROMPT_FILE.exists():
            text = PROMPT_FILE.read_text(encoding="utf-8").strip()
            if text:
                return text
    except Exception as e:  # noqa: BLE001 - never crash on prompt loading
        log(f"[WARN] Could not read {PROMPT_FILE.name}: {e}")
    return ""


def pick_state_file(override: str | None = None) -> Path:
    if override:
        return Path(override)
    if LATEST_GAME_STATE_FILE.exists():
        return LATEST_GAME_STATE_FILE
    return GAME_STATE_FILE


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


def summarize(state: dict) -> str:
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


def build_stdin(state: dict, guide: str) -> str:
    """guide is included only when non-empty (first turn / independent calls)."""
    parts = []
    if guide:
        parts.append("=== DEEPBATTLER STRATEGY GUIDE ===\n" + guide)
    parts.append("=== CURRENT GAME STATE (summary) ===\n" + summarize(state))
    parts.append(
        "=== CURRENT GAME STATE (full JSON) ===\n"
        + json.dumps(state, indent=2, ensure_ascii=False)
    )
    return "\n\n".join(parts) + "\n"


def run_claude(claude_bin, model, stdin_data, timeout, session_id=None, is_first=True):
    """Run one headless claude call. Returns (advice, error).

    session_id=None  -> independent one-off call (persona + guide each time).
    is_first=True    -> create the session (--session-id) and set the persona.
    is_first=False   -> resume the existing conversation (--resume); guide already
                        lives in the conversation history, so don't resend it.
    """
    env = os.environ.copy()
    # Force the Max *subscription* (OAuth). A stray API key would override it and
    # bill per token instead of using the subscription.
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)

    inner = ["-p", INSTRUCTION, "--model", model, "--output-format", "text"]
    if session_id is None:
        inner += ["--append-system-prompt", PERSONA]
    elif is_first:
        inner += ["--session-id", session_id, "--append-system-prompt", PERSONA]
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


def process_state(claude_bin, model, guide, state, speak, timeout, session_id, is_first):
    turn = turn_of(state)
    write_output(f"\U0001f914 Analyzing turn {turn}...")
    include_guide = (session_id is None) or is_first
    stdin_data = build_stdin(state, guide if include_guide else "")
    advice, err = run_claude(
        claude_bin, model, stdin_data, timeout, session_id=session_id, is_first=is_first
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

    use_session = not args.no_session
    guide = load_strategy_guide()
    speak = make_speaker(args.tts)

    log("=" * 66)
    log("DeepBattler -- Claude Code caller (using your Claude Max subscription)")
    log(f"  claude:    {claude_bin}")
    log(f"  model:     {args.model}")
    log(f"  guide:     {PROMPT_FILE if guide else '(built-in default persona only)'}")
    log(f"  watching:  {pick_state_file(args.state_file)}")
    log(f"  output ->  {AGENT_OUTPUT_FILE}")
    log(f"  session:   {'continuous per game (remembers prior turns)' if use_session else 'independent calls'}")
    log(f"  TTS:       {'on' if args.tts else 'off (use --tts for voice)'}")
    if os.environ.get("ANTHROPIC_API_KEY"):
        log("  note:      ANTHROPIC_API_KEY is set but will be IGNORED so calls use\n"
            "             your subscription, not per-token API billing.")
    log("=" * 66)

    if args.once:
        state = load_game_state(pick_state_file(args.state_file))
        if not state:
            log("[INFO] No valid game state available right now.")
            return
        # A one-off check is always an independent call.
        process_state(claude_bin, args.model, guide, state, speak, args.timeout,
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
            state_file = pick_state_file(args.state_file)
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

            # Only act on genuinely new states, and not faster than the cooldown,
            # to be gentle on the subscription usage limit.
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
            process_state(claude_bin, args.model, guide, state, speak, args.timeout,
                          session_id=active_session, is_first=is_first)
    except KeyboardInterrupt:
        log("\nBye! \U0001f37b")


if __name__ == "__main__":
    main()
