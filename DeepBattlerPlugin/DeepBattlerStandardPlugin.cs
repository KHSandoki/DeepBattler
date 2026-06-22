using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Windows.Controls;
using Hearthstone_Deck_Tracker.API;
using Hearthstone_Deck_Tracker.Hearthstone;
using Hearthstone_Deck_Tracker.Hearthstone.Entities;
using Hearthstone_Deck_Tracker.Plugins;
using HearthDb.Enums;
using Hearthstone_Deck_Tracker.Enums;
using Newtonsoft.Json;

namespace DeepBattlerPlugin
{
    // Experimental: serializes Standard / constructed game state to JSON for the
    // Python Claude coach (run: python claude_caller.py --mode standard).
    //
    // This plugin lives in the same DLL as DeepBattlerPlugin, so both load in HDT.
    // The in-game overlay window is created by DeepBattlerPlugin; this one only
    // writes constructed state to real_time_caller/latest_standard_state.json.
    // During a Battlegrounds match there is no single opponent hero, so this
    // plugin naturally stays quiet; during a constructed match the original
    // Battlegrounds plugin stays quiet. The Python side watches only the file
    // for the mode you launched, so the two never collide.
    public class DeepBattlerStandardPlugin : IPlugin
    {
        public string Name => "DeepBattler Standard";
        public string Description => "Serialize Standard/constructed game state for the LLM coach (experimental)";
        public string ButtonText => "Do Nothing";
        public string Author => "DeepBattler";
        public Version Version => new Version(0, 1, 0);
        public MenuItem MenuItem => null;

        private static readonly string _agentRoot = ResolveAgentRoot();
        private readonly string _latestPath = Path.Combine(_agentRoot, "real_time_caller", "latest_standard_state.json");
        private readonly string _statePath = Path.Combine(_agentRoot, "standard_game_state.json");
        private static readonly Encoding _utf8NoBom = new UTF8Encoding(false);
        private static readonly string _logPath = Path.Combine(_agentRoot, "deepbattler_standard.log");

        private string _lastJson = "";
        private string _lastError = "";

        private static string ResolveAgentRoot()
        {
            var overrideDir = Environment.GetEnvironmentVariable("DEEPBATTLER_AGENT_DIR");
            if (!string.IsNullOrEmpty(overrideDir))
                return overrideDir;
            return Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.Desktop),
                "DeepBattler", "Agent");
        }

        private static void Log(string msg)
        {
            try
            {
                File.AppendAllText(_logPath,
                    "[" + DateTime.Now.ToString("HH:mm:ss") + "] " + msg + Environment.NewLine, _utf8NoBom);
            }
            catch { }
        }

        public void OnLoad()
        {
            try { File.WriteAllText(_logPath, "", _utf8NoBom); } catch { }  // fresh log each HDT session
            Log("DeepBattler Standard plugin loaded.");
            Log("agent root: " + _agentRoot);
            Log("writing state to: " + _latestPath);
        }

        public void OnUnload() { }
        public void OnButtonPress() { }

        public void OnUpdate()
        {
            try
            {
                WriteStateIfChanged();
            }
            catch (Exception ex)
            {
                // HDT calls OnUpdate every frame -- only log a NEW/changed error so we don't spam.
                string msg = ex.GetType().Name + ": " + ex.Message;
                if (msg != _lastError)
                {
                    _lastError = msg;
                    Log("ERROR in WriteStateIfChanged: " + msg + Environment.NewLine + ex.StackTrace);
                }
            }
        }

        private void WriteStateIfChanged()
        {
            var game = Core.Game;
            if (game == null)
                return;

            var playerEntity = game.PlayerEntity;
            var playerHero = game.Player?.Hero;
            var opponentHero = game.Opponent?.Hero;
            if (playerEntity == null || playerHero == null || opponentHero == null)
                return;

            int pid = playerEntity.GetTag(GameTag.PLAYER_ID);
            int oid = opponentHero.GetTag(GameTag.CONTROLLER);
            var all = game.Entities.Values;

            int turn = game.GameEntity?.GetTag(GameTag.TURN) ?? 0;
            bool myTurn = playerEntity.GetTag(GameTag.CURRENT_PLAYER) == 1;
            int playerSpellDamage = SpellDamage(game.Player?.Board);
            int opponentSpellDamage = SpellDamage(game.Opponent?.Board);

            var state = new
            {
                game_state = new
                {
                    turn_number = turn,
                    active_player = myTurn ? "player" : "opponent",
                    phase = myTurn ? "PlayerTurn" : "OpponentTurn"
                },
                player = new
                {
                    hero = HeroName(playerHero),
                    @class = ((CardClass)playerHero.GetTag(GameTag.CLASS)).ToString(),
                    health = Health(playerHero),
                    armor = playerHero.GetTag(GameTag.ARMOR),
                    hero_can_attack = playerHero.GetTag(GameTag.EXHAUSTED) == 0 && playerHero.GetTag(GameTag.FROZEN) == 0,
                    mana_available = Math.Max(0, playerEntity.GetTag(GameTag.RESOURCES) - playerEntity.GetTag(GameTag.RESOURCES_USED)),
                    mana_total = playerEntity.GetTag(GameTag.RESOURCES),
                    overloaded_next_turn = playerEntity.GetTag(GameTag.OVERLOAD_OWED),
                    spell_damage = playerSpellDamage,
                    weapon = Weapon(all, pid),
                    hero_power = HeroPower(all, pid),
                    fatigue = playerEntity.GetTag(GameTag.FATIGUE),
                    hand = HandCards(game.Player?.Hand),
                    board = Minions(game.Player?.Board),
                    secrets = KnownSecrets(all, pid),
                    locations = Locations(all, pid),
                    deck_remaining_count = game.Player?.DeckCount ?? DeckCount(all, pid),
                    deck_known_cards = CardObjs(game.Player?.KnownCardsInDeck)
                },
                opponent = new
                {
                    hero = HeroName(opponentHero),
                    @class = ((CardClass)opponentHero.GetTag(GameTag.CLASS)).ToString(),
                    health = Health(opponentHero),
                    armor = opponentHero.GetTag(GameTag.ARMOR),
                    spell_damage = opponentSpellDamage,
                    weapon = Weapon(all, oid),
                    hero_power = HeroPower(all, oid),
                    hand_count = game.Opponent?.Hand?.Count() ?? 0,
                    known_hand_cards = KnownHandCards(game.Opponent?.Hand),
                    board = Minions(game.Opponent?.Board),
                    locations = Locations(all, oid),
                    secrets_count = all.Count(e =>
                        e.GetTag(GameTag.ZONE) == (int)Zone.SECRET &&
                        e.GetTag(GameTag.CONTROLLER) == oid),
                    known_played_cards = OpponentPlayed(all, oid),
                    predicted_deck_cards = CardObjs(game.Opponent?.KnownCardsInDeck)
                }
            };

            string json = JsonConvert.SerializeObject(state, Formatting.Indented);
            if (json == _lastJson)
                return;
            _lastJson = json;
            TryWrite(_statePath, json);
            TryWrite(_latestPath, json);
            Log("wrote turn " + turn + " myTurn=" + myTurn
                + " | you board=" + (game.Player?.Board?.Count() ?? 0) + " hand=" + (game.Player?.Hand?.Count() ?? 0)
                + " | opp board=" + (game.Opponent?.Board?.Count() ?? 0) + " hand=" + (game.Opponent?.Hand?.Count() ?? 0)
                + " knownHand=" + KnownHandCards(game.Opponent?.Hand).Count + " | " + json.Length + " bytes");
        }

        // ---------------------------------------------------------------- helpers

        private static int Health(Entity hero) =>
            hero.GetTag(GameTag.HEALTH) - hero.GetTag(GameTag.DAMAGE);

        private static int SpellDamage(IEnumerable<Entity> board) =>
            board == null ? 0 : board.Where(e => e != null && e.Card != null).Sum(e => e.GetTag(GameTag.SPELLPOWER));

        private static string HeroName(Entity hero)
        {
            var name = hero?.Card?.Name;
            return string.IsNullOrEmpty(name) ? "Unknown" : name;
        }

        private static string Clean(string text) =>
            string.IsNullOrEmpty(text) ? "" : text.Replace("\r", " ").Replace("\n", " ").Trim();

        private static string CardTypeStr(Entity e)
        {
            switch ((CardType)e.GetTag(GameTag.CARDTYPE))
            {
                case CardType.MINION: return "Minion";
                case CardType.SPELL: return "Spell";
                case CardType.WEAPON: return "Weapon";
                case CardType.HERO: return "Hero";
                default: return "";
            }
        }

        private static List<object> Minions(IEnumerable<Entity> board)
        {
            var list = new List<object>();
            if (board == null)
                return list;
            foreach (var e in board)
            {
                if (e?.Card == null || e.GetTag(GameTag.CARDTYPE) != (int)CardType.MINION)
                    continue;
                list.Add(new
                {
                    name = e.Card.Name ?? "",
                    attack = e.GetTag(GameTag.ATK),
                    health = e.GetTag(GameTag.HEALTH) - e.GetTag(GameTag.DAMAGE),
                    taunt = e.GetTag(GameTag.TAUNT) == 1,
                    divine_shield = e.GetTag(GameTag.DIVINE_SHIELD) == 1,
                    stealth = e.GetTag(GameTag.STEALTH) == 1,
                    poisonous = e.GetTag(GameTag.POISONOUS) == 1,
                    frozen = e.GetTag(GameTag.FROZEN) == 1,
                    windfury = e.GetTag(GameTag.WINDFURY) == 1,
                    rush = e.GetTag(GameTag.RUSH) == 1,
                    charge = e.GetTag(GameTag.CHARGE) == 1,
                    lifesteal = e.GetTag(GameTag.LIFESTEAL) == 1,
                    reborn = e.GetTag(GameTag.REBORN) == 1,
                    position = e.GetTag(GameTag.ZONE_POSITION),
                    summoned_this_turn = e.GetTag(GameTag.NUM_TURNS_IN_PLAY) == 0,
                    ready = e.GetTag(GameTag.EXHAUSTED) == 0 && e.GetTag(GameTag.ATK) > 0 && e.GetTag(GameTag.FROZEN) == 0,
                    description = Clean(e.Card.Text)
                });
            }
            return list;
        }

        private static List<object> HandCards(IEnumerable<Entity> hand)
        {
            var list = new List<object>();
            if (hand == null)
                return list;
            foreach (var e in hand)
            {
                if (e?.Card == null || string.IsNullOrEmpty(e.Card.Name))
                    continue;
                if (e.GetTag(GameTag.CARDTYPE) == (int)CardType.HERO)
                    continue;
                int cost = e.GetTag(GameTag.COST);
                if (cost <= 0)
                    cost = e.Card.Cost;
                list.Add(new
                {
                    name = e.Card.Name,
                    cost = cost,
                    type = CardTypeStr(e),
                    description = Clean(e.Card.Text)
                });
            }
            return list;
        }

        private static object Weapon(IEnumerable<Entity> all, int controller)
        {
            var w = all.FirstOrDefault(e =>
                e.GetTag(GameTag.CONTROLLER) == controller &&
                e.GetTag(GameTag.ZONE) == (int)Zone.PLAY &&
                e.GetTag(GameTag.CARDTYPE) == (int)CardType.WEAPON &&
                e.Card != null);
            if (w == null)
                return null;
            return new
            {
                name = w.Card.Name ?? "",
                attack = w.GetTag(GameTag.ATK),
                durability = w.GetTag(GameTag.DURABILITY) - w.GetTag(GameTag.DAMAGE)
            };
        }

        private static object HeroPower(IEnumerable<Entity> all, int controller)
        {
            var hp = all.FirstOrDefault(e =>
                e.GetTag(GameTag.CONTROLLER) == controller &&
                e.GetTag(GameTag.CARDTYPE) == (int)CardType.HERO_POWER &&
                e.Card != null);
            if (hp == null)
                return null;
            return new
            {
                name = hp.Card.Name ?? "",
                cost = hp.GetTag(GameTag.COST),
                description = Clean(hp.Card.Text),
                used = hp.GetTag(GameTag.EXHAUSTED) == 1
            };
        }

        private static List<object> KnownSecrets(IEnumerable<Entity> all, int controller)
        {
            var list = new List<object>();
            foreach (var e in all.Where(x =>
                x.GetTag(GameTag.ZONE) == (int)Zone.SECRET &&
                x.GetTag(GameTag.CONTROLLER) == controller &&
                x.Card != null && !string.IsNullOrEmpty(x.Card.Name)))
            {
                list.Add(new { name = e.Card.Name, description = Clean(e.Card.Text) });
            }
            return list;
        }

        private static int DeckCount(IEnumerable<Entity> all, int controller) =>
            all.Count(e =>
                e.GetTag(GameTag.ZONE) == (int)Zone.DECK &&
                e.GetTag(GameTag.CONTROLLER) == controller);

        private static List<object> DeckKnown(IEnumerable<Entity> all, int controller)
        {
            return all.Where(e =>
                    e.GetTag(GameTag.ZONE) == (int)Zone.DECK &&
                    e.GetTag(GameTag.CONTROLLER) == controller &&
                    e.Card != null && !string.IsNullOrEmpty(e.Card.Name))
                .GroupBy(e => e.Card.Name)
                .Select(g => (object)new { name = g.Key, cost = g.First().Card.Cost, count = g.Count() })
                .ToList();
        }

        private static List<object> OpponentPlayed(IEnumerable<Entity> all, int controller)
        {
            // Approximation of "cards the opponent has revealed": minions/spells/weapons
            // they control that are on the board, dead, or revealed as secrets.
            var zones = new[] { (int)Zone.PLAY, (int)Zone.GRAVEYARD, (int)Zone.SECRET };
            return all.Where(e =>
                    e.GetTag(GameTag.CONTROLLER) == controller &&
                    e.Card != null && !string.IsNullOrEmpty(e.Card.Name) &&
                    zones.Contains(e.GetTag(GameTag.ZONE)) &&
                    e.GetTag(GameTag.CARDTYPE) != (int)CardType.HERO &&
                    e.GetTag(GameTag.CARDTYPE) != (int)CardType.HERO_POWER &&
                    e.GetTag(GameTag.CARDTYPE) != (int)CardType.PLAYER)
                .GroupBy(e => e.Card.Name)
                .Select(g => (object)new { name = g.Key, cost = g.First().Card.Cost })
                .ToList();
        }

        // Cards HDT has identified in a hand (opponent hidden cards are skipped).
        private static List<object> KnownHandCards(IEnumerable<Entity> hand)
        {
            var list = new List<object>();
            if (hand == null)
                return list;
            foreach (var e in hand)
            {
                if (e?.Card == null || string.IsNullOrEmpty(e.Card.Name))
                    continue; // unknown / hidden card
                int cost = e.GetTag(GameTag.COST);
                if (cost <= 0)
                    cost = e.Card.Cost;
                list.Add(new { name = e.Card.Name, cost = cost });
            }
            return list;
        }

        // HDT Card list (KnownCardsInDeck / predictions) -> name/cost/count objects.
        private static List<object> CardObjs(IEnumerable<Card> cards)
        {
            var list = new List<object>();
            if (cards == null)
                return list;
            foreach (var c in cards)
            {
                if (c == null || string.IsNullOrEmpty(c.Name))
                    continue;
                list.Add(new { name = c.Name, cost = c.Cost, count = c.Count });
            }
            return list;
        }

        private static List<object> Locations(IEnumerable<Entity> all, int controller)
        {
            var list = new List<object>();
            foreach (var e in all.Where(x => x.IsLocation
                && x.GetTag(GameTag.CONTROLLER) == controller
                && x.GetTag(GameTag.ZONE) == (int)Zone.PLAY
                && x.Card != null && !string.IsNullOrEmpty(x.Card.Name)))
            {
                list.Add(new { name = e.Card.Name, description = Clean(e.Card.Text) });
            }
            return list;
        }

        private static void TryWrite(string path, string json)
        {
            try
            {
                var dir = Path.GetDirectoryName(path);
                if (!string.IsNullOrEmpty(dir))
                    Directory.CreateDirectory(dir);
                File.WriteAllText(path, json, _utf8NoBom);
            }
            catch (Exception ex)
            {
                Log("ERROR writing " + path + ": " + ex.Message);
            }
        }
    }
}
