"""
HORSE RACING AI - RSI ANALYST SYSTEM
Deterministic, production-safe horse racing analysis with RSI ratings
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Callable, Any
from datetime import datetime, timezone, timedelta
AEDT = timezone(timedelta(hours=11))  # Australian Eastern Daylight Time (UTC+11)
import statistics
import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv
import time
import io
import sys
import json
import threading
from functools import wraps
import re


def retry_on_network_error(max_retries: int = 3, backoff_base: float = 2.0):
    """
    Decorator to retry function on network errors with exponential backoff
    Handles connection resets when Mac lid is closed
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout,
                        ConnectionResetError) as e:
                    if attempt == max_retries - 1:
                        # Last attempt failed
                        print(f"⚠ Network error after {max_retries} attempts: {e}")
                        return None if 'return' in func.__annotations__ and func.__annotations__['return'] != bool else False

                    # Exponential backoff
                    wait_time = backoff_base ** attempt
                    print(f"⚠ Network error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                except Exception as e:
                    # Non-network errors should not retry
                    print(f"Error in {func.__name__}: {e}")
                    return None if 'return' in func.__annotations__ and func.__annotations__['return'] != bool else False

            return None if 'return' in func.__annotations__ and func.__annotations__['return'] != bool else False

        return wrapper
    return decorator




class BetTracker:
    """Track bets and results persistently in a JSON file"""

    def __init__(self, storage_path: str = None):
        if storage_path is None:
            # Use Railway volume if available, otherwise local file
            if os.path.exists("/data"):
                storage_path = "/data/bets.json"
            else:
                storage_path = os.path.expanduser("~/horse_tipper_bets.json")
        self.storage_path = storage_path
        print(f"📁 Bet storage: {self.storage_path}")
        self.bets = self._load_bets()

    def _load_bets(self) -> List[Dict]:
        """Load bets from JSON file, seeding from backtest data if empty"""
        bets = []
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    bets = json.load(f)
            except (json.JSONDecodeError, IOError):
                bets = []

        # Merge backtest seed data (skip any IDs already present)
        seed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_seed.json")
        if os.path.exists(seed_path):
            try:
                with open(seed_path, 'r') as f:
                    seed_bets = json.load(f)
                existing_ids = {b.get("id") for b in bets}
                new_bets = [b for b in seed_bets if b.get("id") not in existing_ids]
                if new_bets:
                    bets.extend(new_bets)
                    print(f"  Merged {len(new_bets)} backtest bets from seed ({len(seed_bets)} total in seed, {len(existing_ids)} already existed)")
                    self.bets = bets
                    self._save_bets()
            except (json.JSONDecodeError, IOError):
                pass

        return bets

    def _save_bets(self):
        """Save bets to JSON file"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.bets, f, indent=2, default=str)
        except IOError as e:
            print(f"Error saving bets: {e}")

    def record_bet(self, track: str, race_num: int, horse_name: str, horse_num: int,
                   price: float, units: float, rsi: int, is_tracked: bool,
                   race_time: datetime, market_rank: int = 999) -> str:
        """Record a new bet and return its ID"""
        bet_id = f"{track}_R{race_num}_{race_time.strftime('%Y%m%d_%H%M')}"

        bet = {
            "id": bet_id,
            "track": track,
            "race_num": race_num,
            "horse_name": horse_name,
            "horse_num": horse_num,
            "price": price,
            "units": units,
            "rsi": rsi,
            "is_tracked": is_tracked,
            "market_rank": market_rank,
            "race_time": race_time.isoformat(),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "result": None,  # "win", "loss", or None (pending)
            "finishing_position": None,
            "settled_at": None,
        }

        # Check for duplicate
        for existing in self.bets:
            if existing.get("id") == bet_id:
                return bet_id  # Already recorded

        self.bets.append(bet)
        self._save_bets()
        return bet_id

    def settle_bet(self, bet_id: str, finishing_position: int) -> bool:
        """Settle a bet with the finishing position"""
        for bet in self.bets:
            if bet.get("id") == bet_id:
                bet["finishing_position"] = finishing_position
                bet["result"] = "win" if finishing_position == 1 else "loss"
                bet["settled_at"] = datetime.now(timezone.utc).isoformat()
                self._save_bets()
                return True
        return False

    def get_bets_in_period(self, days: int = None, period: str = None) -> List[Dict]:
        """Get bets within a time period"""
        now = datetime.now(timezone.utc)

        if period == "daily":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "monthly":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "yearly":
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif days:
            start = now - timedelta(days=days)
        else:
            return self.bets

        filtered = []
        for bet in self.bets:
            try:
                bet_time = datetime.fromisoformat(bet.get("race_time", "").replace('Z', '+00:00'))
                if bet_time >= start:
                    filtered.append(bet)
            except (ValueError, TypeError):
                continue

        return filtered

    def get_pending_bets(self) -> List[Dict]:
        """Get all pending (unsettled) bets"""
        return [b for b in self.bets if b.get("result") is None]

    def settle_bet_by_horse(self, track: str, race_num: int, horse_name: str, position: int) -> bool:
        """Settle a bet by matching track, race number, and horse name"""
        horse_lower = horse_name.lower().strip()

        for bet in self.bets:
            if bet.get("result") is not None:
                continue  # Already settled

            bet_track = bet.get("track", "").lower()
            bet_race = bet.get("race_num", 0)
            bet_horse = bet.get("horse_name", "").lower().strip()

            # Match by track, race number, and horse name
            if (track.lower() in bet_track or bet_track in track.lower()) and \
               bet_race == race_num and \
               (horse_lower in bet_horse or bet_horse in horse_lower):
                bet["finishing_position"] = position
                bet["result"] = "win" if position == 1 else "loss"
                bet["settled_at"] = datetime.now(timezone.utc).isoformat()
                self._save_bets()
                return True
        return False

    def settle_as_scratched(self, track: str, race_num: int, horse_name: str) -> bool:
        """Mark a bet as scratched (void/refund) - horse not in race results"""
        horse_lower = horse_name.lower().strip()

        for bet in self.bets:
            if bet.get("result") is not None:
                continue  # Already settled

            bet_track = bet.get("track", "").lower()
            bet_race = bet.get("race_num", 0)
            bet_horse = bet.get("horse_name", "").lower().strip()

            if (track.lower() in bet_track or bet_track in track.lower()) and \
               bet_race == race_num and \
               (horse_lower in bet_horse or bet_horse in horse_lower):
                bet["finishing_position"] = 0
                bet["result"] = "scratched"  # Void - stake refunded
                bet["settled_at"] = datetime.now(timezone.utc).isoformat()
                self._save_bets()
                return True

        return False

    def calculate_stats(self, bets: List[Dict], tracked_only: bool = False, market_rank_filter: int = None) -> Dict:
        """Calculate statistics for a list of bets"""
        if tracked_only:
            bets = [b for b in bets if b.get("is_tracked")]

        if market_rank_filter is not None:
            bets = [b for b in bets if b.get("market_rank") == market_rank_filter]

        if not bets:
            return {
                "total_bets": 0,
                "settled": 0,
                "pending": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "total_staked": 0.0,
                "total_return": 0.0,
                "profit": 0.0,
                "roi": 0.0,
                "avg_odds": 0.0
            }

        settled = [b for b in bets if b.get("result") is not None]
        pending = [b for b in bets if b.get("result") is None]
        wins = [b for b in settled if b.get("result") == "win"]
        losses = [b for b in settled if b.get("result") == "loss"]
        scratched = [b for b in settled if b.get("result") == "scratched"]

        # Exclude scratched bets from staked (they're refunded)
        active_settled = [b for b in settled if b.get("result") != "scratched"]

        # Calculate staked and returns
        total_staked = 0.0
        total_return = 0.0
        for b in active_settled:
            units = b.get("units", 0)
            if b.get("result") == "win":
                total_staked += units
                total_return += units * b.get("price", 0)
            elif b.get("result") == "loss":
                total_staked += units
        profit = total_return - total_staked

        # Win rate based on active bets only (not scratched)
        win_rate = (len(wins) / len(active_settled) * 100) if active_settled else 0.0
        roi = (profit / total_staked * 100) if total_staked > 0 else 0.0

        # Calculate average odds from all bets
        all_prices = [b.get("price", 0) for b in bets if b.get("price", 0) > 0]
        avg_odds = sum(all_prices) / len(all_prices) if all_prices else 0.0

        return {
            "total_bets": len(bets),
            "settled": len(settled),
            "pending": len(pending),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 1),
            "total_staked": round(total_staked, 2),
            "total_return": round(total_return, 2),
            "profit": round(profit, 2),
            "roi": round(roi, 2),
            "avg_odds": round(avg_odds, 2)
        }


class DiscordNotifier:
    """Send notifications to Discord via bot token"""

    def __init__(self, bot_token: str, channel_id: str):
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.base_url = "https://discord.com/api/v10"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bot {bot_token}",
            "Content-Type": "application/json"
        })

    @retry_on_network_error(max_retries=3, backoff_base=2.0)
    def send_tip(self, race_time: str, track: str, race_num: int, distance: int,
                 surface: str, horse_num: int, horse_name: str, price: float,
                 units: float, rsi: int, is_tracked: bool = False, market_rank: int = 999):
        """Send a formatted tip to Discord with retry logic"""
        if not self.bot_token or not self.channel_id:
            return False

        # BEST BET = market rank 1 (favorite), EDGE BET = rank 2-3
        is_best_bet = market_rank == 1
        color = 0xFF4500 if is_best_bet else 0x00FF00  # Orange-red for BEST BET, Green for EDGE BET

        title = f"🔥 BEST BET | {track} R{race_num}" if is_best_bet else f"📊 EDGE BET | {track} R{race_num}"

        fields = [
            {"name": "⏰ Race Time", "value": race_time, "inline": True},
            {"name": "📏 Distance", "value": f"{distance}m", "inline": True},
            {"name": "🌿 Surface", "value": surface, "inline": True},
            {"name": "🐴 Selection", "value": f"**{horse_num}. {horse_name}**", "inline": False},
            {"name": "💰 Odds", "value": f"${price:.2f}", "inline": True},
            {"name": "📊 Units", "value": f"{units}u", "inline": True},
            {"name": "📈 RSI", "value": f"{rsi}%", "inline": True},
        ]

        # Add market rank for BEST BETs
        if is_best_bet:
            fields.append({"name": "🏆 Market Rank", "value": "Favorite (Rank 1)", "inline": True})

        footer_text = "Horse Tipper | 🔥 BEST BET" if is_best_bet else "Horse Tipper | 📊 EDGE BET"

        embed = {
            "title": title,
            "color": color,
            "fields": fields,
            "footer": {"text": footer_text}
        }

        payload = {"embeds": [embed]}
        url = f"{self.base_url}/channels/{self.channel_id}/messages"
        response = self.session.post(url, json=payload, timeout=10)
        return response.status_code == 200

    @retry_on_network_error(max_retries=3, backoff_base=2.0)
    def send_message(self, content: str):
        """Send a simple text message to Discord with retry logic"""
        if not self.bot_token or not self.channel_id:
            return False

        url = f"{self.base_url}/channels/{self.channel_id}/messages"
        response = self.session.post(url, json={"content": content}, timeout=10)
        return response.status_code == 200

    @retry_on_network_error(max_retries=3, backoff_base=2.0)
    def send_results_embed(self, period: str, overall_stats: Dict, best_bet_stats: Dict = None, edge_bet_stats: Dict = None):
        """Send a formatted results embed to Discord with retry logic"""
        if not self.bot_token or not self.channel_id:
            return False

        # Period display names
        period_names = {
            "daily": "📅 Today's Results",
            "weekly": "📆 Weekly Results",
            "monthly": "🗓️ Monthly Results",
            "yearly": "📊 Yearly Results",
            "lifetime": "📊 Lifetime Results"
        }

        title = period_names.get(period, f"📊 {period.title()} Results")

        # Determine color based on total profit
        total_profit = overall_stats["profit"]
        if total_profit > 0:
            color = 0x00FF00  # Green for profit
        elif total_profit < 0:
            color = 0xFF0000  # Red for loss
        else:
            color = 0x3498DB  # Blue for break-even

        # Build fields with separate sections
        fields = []

        # BEST BETS section
        if best_bet_stats and best_bet_stats["total_bets"] > 0:
            fields.append({"name": "🔥 BEST BETS (Rank 1 Favorites)", "value": "━━━━━━━━━━━━━━━━━━━━", "inline": False})
            fields.extend([
                {"name": "Bets", "value": str(best_bet_stats["total_bets"]), "inline": True},
                {"name": "Wins", "value": f"{best_bet_stats['wins']} ({best_bet_stats['win_rate']}%)", "inline": True},
                {"name": "P/L", "value": f"{best_bet_stats['profit']:+.2f}u", "inline": True},
                {"name": "ROI", "value": f"{best_bet_stats['roi']:+.1f}%", "inline": True},
                {"name": "Avg Odds", "value": f"${best_bet_stats['avg_odds']:.2f}", "inline": True},
                {"name": "\u200b", "value": "\u200b", "inline": True},
            ])

        # EDGE BETS section
        if edge_bet_stats and edge_bet_stats["total_bets"] > 0:
            fields.append({"name": "📊 EDGE BETS (Rank 2-3)", "value": "━━━━━━━━━━━━━━━━━━━━", "inline": False})
            fields.extend([
                {"name": "Bets", "value": str(edge_bet_stats["total_bets"]), "inline": True},
                {"name": "Wins", "value": f"{edge_bet_stats['wins']} ({edge_bet_stats['win_rate']}%)", "inline": True},
                {"name": "P/L", "value": f"{edge_bet_stats['profit']:+.2f}u", "inline": True},
                {"name": "ROI", "value": f"{edge_bet_stats['roi']:+.1f}%", "inline": True},
                {"name": "Avg Odds", "value": f"${edge_bet_stats['avg_odds']:.2f}", "inline": True},
                {"name": "\u200b", "value": "\u200b", "inline": True},
            ])

        # OVERALL section
        fields.append({"name": "📊 OVERALL", "value": "━━━━━━━━━━━━━━━━━━━━", "inline": False})
        fields.extend([
            {"name": "Total Bets", "value": str(overall_stats["total_bets"]), "inline": True},
            {"name": "Wins", "value": f"{overall_stats['wins']} ({overall_stats['win_rate']}%)", "inline": True},
            {"name": "P/L", "value": f"{overall_stats['profit']:+.2f}u", "inline": True},
            {"name": "ROI", "value": f"{overall_stats['roi']:+.1f}%", "inline": True},
            {"name": "Staked", "value": f"{overall_stats['total_staked']:.2f}u", "inline": True},
            {"name": "Return", "value": f"{overall_stats['total_return']:.2f}u", "inline": True},
        ])

        embed = {
            "title": title,
            "color": color,
            "fields": fields,
            "footer": {"text": f"Horse Tipper | 🔥 BEST BET • 📊 EDGE BET • Generated {datetime.now(AEDT).strftime('%H:%M')}"}
        }

        payload = {"embeds": [embed]}
        url = f"{self.base_url}/channels/{self.channel_id}/messages"
        response = self.session.post(url, json=payload, timeout=10)
        return response.status_code == 200

    @retry_on_network_error(max_retries=3, backoff_base=2.0)
    def get_recent_messages(self, limit: int = 10) -> List[Dict]:
        """Get recent messages from the channel to check for commands with retry logic"""
        if not self.bot_token or not self.channel_id:
            return []

        url = f"{self.base_url}/channels/{self.channel_id}/messages?limit={limit}"
        response = self.session.get(url, timeout=10)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            print("⚠ Discord: Bot lacks permission to read messages. Enable 'Read Message History' in bot permissions.")
            return []
        else:
            print(f"⚠ Discord API error: {response.status_code}")
            return []


class DiscordCommandHandler:
    """Handle Discord commands for results"""

    COMMANDS = {
        "!daily": "daily",
        "!weekly": "weekly",
        "!monthly": "monthly",
        "!yearly": "yearly",
        "!results": "daily",  # Alias for daily
        "!stats": "weekly",   # Alias for weekly
        "!bets": "bets",      # Show recent bets
        "!pending": "pending", # Show pending bets
        "!help": "help",
        "!lifetime": "lifetime",
    }

    def __init__(self, discord: 'DiscordNotifier', bet_tracker: 'BetTracker'):
        self.discord = discord
        self.bet_tracker = bet_tracker
        self.processed_messages = set()
        self.running = False
        self.thread = None

    def start(self):
        """Start the command handler in a background thread"""
        if self.running:
            return

        # Mark existing messages as processed so we only respond to NEW commands
        existing_messages = self.discord.get_recent_messages(limit=50)
        for msg in existing_messages:
            self.processed_messages.add(msg.get("id"))
        print(f"  Marked {len(existing_messages)} existing messages as processed")

        self.running = True
        self.thread = threading.Thread(target=self._poll_commands, daemon=True)
        self.thread.start()
        print("✓ Discord command handler started (listening for commands...)")

    def stop(self):
        """Stop the command handler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _poll_commands(self):
        """Poll for new commands every 3 seconds"""
        while self.running:
            try:
                messages = self.discord.get_recent_messages(limit=10)

                for msg in messages:
                    msg_id = msg.get("id")

                    # Skip if already processed
                    if msg_id in self.processed_messages:
                        continue

                    # Mark as processed immediately
                    self.processed_messages.add(msg_id)

                    # Skip bot messages
                    if msg.get("author", {}).get("bot"):
                        continue

                    content = msg.get("content", "").strip().lower()
                    author = msg.get("author", {}).get("username", "unknown")

                    # Debug: show all new messages
                    print(f"📨 New message from {author}: '{content}'")

                    # Check for commands
                    if content in self.COMMANDS:
                        command_type = self.COMMANDS[content]
                        print(f"📩 Command received: {content}")

                        if command_type == "help":
                            self._send_help()
                        elif command_type == "bets":
                            self._send_recent_bets()
                        elif command_type == "pending":
                            self._send_pending_bets()
                        else:
                            self._send_results(command_type)

                # Keep processed list manageable
                if len(self.processed_messages) > 1000:
                    self.processed_messages = set(list(self.processed_messages)[-500:])

            except Exception as e:
                print(f"Command handler error: {e}")

            time.sleep(3)  # Check every 3 seconds

    def _merge_stats(self, stats1: Dict, stats2: Dict) -> Dict:
        """Merge two stats dictionaries"""
        if stats1["total_bets"] == 0:
            return stats2
        if stats2["total_bets"] == 0:
            return stats1

        total_staked = stats1["total_staked"] + stats2["total_staked"]
        total_return = stats1["total_return"] + stats2["total_return"]
        profit = total_return - total_staked
        roi = (profit / total_staked * 100) if total_staked > 0 else 0.0

        total_bets = stats1["total_bets"] + stats2["total_bets"]
        wins = stats1["wins"] + stats2["wins"]
        losses = stats1["losses"] + stats2["losses"]
        settled = wins + losses
        win_rate = (wins / settled * 100) if settled > 0 else 0.0

        return {
            "total_bets": total_bets,
            "settled": settled,
            "pending": stats1["pending"] + stats2["pending"],
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 1),
            "total_staked": round(total_staked, 2),
            "total_return": round(total_return, 2),
            "profit": round(profit, 2),
            "roi": round(roi, 1),
            "avg_odds": round((stats1["avg_odds"] * stats1["total_bets"] + stats2["avg_odds"] * stats2["total_bets"]) / total_bets, 2)
        }

    def _send_results(self, period: str):
        """Send results for the specified period"""
        bets = self.bet_tracker.get_bets_in_period(period=period)

        # Calculate separate stats for BEST BETs and EDGE BETs
        best_bet_stats = self.bet_tracker.calculate_stats(bets, market_rank_filter=1)
        rank2_stats = self.bet_tracker.calculate_stats(bets, market_rank_filter=2)
        rank3_stats = self.bet_tracker.calculate_stats(bets, market_rank_filter=3)
        edge_bet_stats = self._merge_stats(rank2_stats, rank3_stats)

        overall_stats = self.bet_tracker.calculate_stats(bets)

        self.discord.send_results_embed(period, overall_stats, best_bet_stats, edge_bet_stats)

        print(f"📊 Sent {period} results to Discord")

    def _send_recent_bets(self):
        """Send list of recent bets"""
        bets = self.bet_tracker.get_bets_in_period(period="daily")

        if not bets:
            self.discord.send_message("📋 No bets recorded today.")
            return

        # Build message
        lines = ["**📋 Today's Bets**\n"]
        for bet in bets[-10:]:  # Last 10 bets
            status = "⏳" if bet.get("result") is None else ("✅" if bet.get("result") == "win" else "❌")
            bet_type = " [EDGE]" if bet.get("is_tracked") else ""
            lines.append(f"{status} {bet['track']} R{bet['race_num']} - {bet['horse_name']} @ ${bet['price']:.2f} ({bet['units']}u){bet_type}")

        self.discord.send_message("\n".join(lines))

    def _send_pending_bets(self):
        """Send list of pending (unsettled) bets"""
        all_bets = self.bet_tracker.bets
        pending = [b for b in all_bets if b.get("result") is None]

        if not pending:
            self.discord.send_message("✅ No pending bets!")
            return

        # Build message
        lines = ["**⏳ Pending Bets**\n"]
        for bet in pending[-15:]:  # Last 15 pending
            bet_type = " [EDGE]" if bet.get("is_tracked") else ""
            try:
                race_time = datetime.fromisoformat(bet.get("race_time", "").replace('Z', '+00:00'))
                time_str = race_time.astimezone(AEDT).strftime('%H:%M')
            except:
                time_str = "??:??"
            lines.append(f"⏰ {time_str} | {bet['track']} R{bet['race_num']} - {bet['horse_name']} @ ${bet['price']:.2f}{bet_type}")

        self.discord.send_message("\n".join(lines))

    def _send_help(self):
        """Send help message"""
        help_text = """**🏇 Horse Tipper Commands**

**Results:**
`!daily` - Today's results
`!weekly` - This week's results
`!monthly` - This month's results
`!yearly` - This year's results
`!lifetime` - All time results

**Bets:**
`!bets` - Show today's bets
`!pending` - Show pending (unsettled) bets

**Aliases:**
`!results` - Same as !daily
`!stats` - Same as !weekly

**Mode:**
**EDGE BETS ONLY** 🎯 - High confidence selections meeting strict RSI + market rank criteria
- RSI 65-78+ required (varies by odds)
- Must be top 1-5 in market (varies by odds)
- Stakes: 1/2 Kelly Criterion (0.5u - 5.0u based on edge)"""

        self.discord.send_message(help_text)


@dataclass
class Runner:
    """Represents a horse runner in a race"""
    saddlecloth: int
    name: str
    price: float  # Decimal odds (e.g., 3.50)

    # Form data (these would come from your API)
    recent_form: str = ""
    class_rating: int = 0
    speed_rating: int = 0
    jockey: str = ""
    trainer: str = ""
    barrier: int = 0
    weight: float = 0.0
    last_starts: List[int] = None  # [1, 3, 2, 5] etc.

    def __post_init__(self):
        if self.last_starts is None:
            self.last_starts = []


@dataclass
class Race:
    """Represents a horse race"""
    track_name: str
    race_number: int
    distance: int  # In meters
    surface: str  # "Turf", "Dirt", "Synthetic"
    grade: str  # Class/grade
    runners: List[Runner]
    start_time: Optional[datetime] = None  # Race start time

    def is_valid(self) -> bool:
        """Check if race has complete data"""
        if not self.runners:
            return False

        for runner in self.runners:
            # Must have price and basic data
            if runner.price <= 0 or not runner.name:
                return False

        return True


class RacingAPIClient:
    """
    Client for The Racing API
    Handles authentication and data fetching
    """

    def __init__(self, username: str, password: str):
        self.base_url = "https://api.theracingapi.com/v1"
        self.auth = HTTPBasicAuth(username, password)
        self.session = requests.Session()
        self.session.auth = self.auth

    @retry_on_network_error(max_retries=3, backoff_base=2.0)
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated API request with error handling and retry logic"""
        url = f"{self.base_url}/{endpoint}"
        response = self.session.get(url, params=params or {}, timeout=15)
        response.raise_for_status()
        return response.json()

    def get_regions(self) -> Dict:
        """Get racing regions"""
        return self._make_request("courses/regions")

    def get_courses(self) -> Dict:
        """Get all courses/tracks"""
        return self._make_request("courses")

    def get_racecards(self) -> Dict:
        """Get today's racecards (free tier)"""
        return self._make_request("racecards/free")

    def get_results(self) -> Dict:
        """Get today's results (free tier)"""
        return self._make_request("results/today/free")

    # ========================================
    # AUSTRALIA PREMIUM API ENDPOINTS
    # ========================================

    def get_australia_meets(self) -> Dict:
        """Get all Australian meetings (Premium Australia plan)"""
        return self._make_request("australia/meets")

    def get_australia_meet_races(self, meet_id: str) -> Dict:
        """Get all races for a specific Australian meeting (Premium)"""
        return self._make_request(f"australia/meets/{meet_id}/races")

    def get_australia_race_detail(self, meet_id: str, race_number: int) -> Dict:
        """Get detailed race information (Premium Australia plan)"""
        return self._make_request(f"australia/meets/{meet_id}/races/{race_number}")

    def get_race_result(self, track_name: str, race_number: int) -> Optional[Dict]:
        """
        Get result for a specific race by checking meets data
        Returns dict with 'winner' and 'positions' if race has finished
        """
        # Get meets data and find the race with Results status
        meets_data = self.get_australia_meets()

        if not meets_data or 'meets' not in meets_data:
            return None

        # Normalize track name (remove sponsor prefixes like "bet365")
        track_lower = track_name.lower()
        # Extract core track name (last word usually)
        track_words = track_lower.replace('bet365', '').replace('@', ' ').split()
        core_track = track_words[-1] if track_words else track_lower

        for meet in meets_data.get('meets', []):
            course = meet.get('course', '').lower()
            meet_id = meet.get('meet_id')

            # Check if track matches (flexible matching)
            course_words = course.replace('bet365', '').replace('@', ' ').split()
            core_course = course_words[-1] if course_words else course

            if core_track not in course and core_course not in track_lower:
                continue

            # Look for the race
            for race in meet.get('races', []):
                # Handle race_number as string or int
                api_race_num = int(race.get('race_number', 0))
                if api_race_num == int(race_number):
                    # Check if race has finished
                    if race.get('race_status') != 'Results':
                        return None  # Race not finished yet

                    # Get detailed race data with positions
                    race_detail = self.get_australia_race_detail(meet_id, race_number)

                    if not race_detail or 'runners' not in race_detail:
                        return None

                    positions = {}
                    winner = None

                    for runner in race_detail.get('runners', []):
                        horse_name = runner.get('horse', '')
                        position = runner.get('position') or runner.get('finish_position') or 0

                        if position:
                            positions[horse_name.lower()] = int(position)
                            if int(position) == 1:
                                winner = horse_name

                    if positions:
                        return {
                            'winner': winner,
                            'positions': positions,
                            'track': meet.get('course'),
                            'race_number': race_number
                        }

        return None

    def parse_australia_to_races(self, meets_data: Dict) -> List['Race']:
        """Parse Premium Australia API data into Race objects"""
        races = []

        if not meets_data or 'meets' not in meets_data:
            return races

        print("Using Premium Australia API data...")

        for meet in meets_data.get('meets', []):
            try:
                meet_id = meet.get('meet_id')  # Note: key is 'meet_id' not 'id'
                track_name = meet.get('course', 'Unknown')  # Note: key is 'course' not 'name'

                # Races are already embedded in the meet, but we need runner details
                embedded_races = meet.get('races', [])

                print(f"\n{track_name} ({len(embedded_races)} races):")

                for embedded_race in embedded_races:
                    try:
                        race_number = int(embedded_race.get('race_number', 0))

                        # Skip trials and jump outs (practice races, not official betting races)
                        if embedded_race.get('is_trial') or embedded_race.get('is_jump_out'):
                            print(f"  R{race_number}: SKIPPED (trial/jump out)")
                            continue

                        race_status = embedded_race.get('race_status', '')

                        # Only process races with confirmed fields and real odds
                        # Nominations/Weights = unconfirmed fields, default $5.00 prices
                        accept_statuses = ['FinalFields', 'Final', 'Interim', 'Open', 'Going']
                        print(f"  R{race_number}: status={race_status}")
                        if race_status in accept_statuses:
                            # Get detailed race data with runners
                            print(f"  Fetching R{race_number} details...")
                            race_detail = self.get_australia_race_detail(meet_id, race_number)

                            if not race_detail or 'runners' not in race_detail:
                                print(f"    ⚠️  No runner data for R{race_number}")
                                continue

                            # Double-check for trials (some APIs don't flag them in embedded data)
                            race_name = (race_detail.get('race_name') or '').upper()
                            race_class = (race_detail.get('class') or '').upper()
                            if (race_detail.get('is_trial') or
                                race_detail.get('is_jump_out') or
                                'TRIAL' in race_name or
                                'JUMP OUT' in race_name or
                                'JUMPOUT' in race_name or
                                'TRIAL' in race_class):
                                print(f"    ⚠️  R{race_number}: SKIPPED (trial race)")
                                continue

                            # Parse start time from API
                            start_time = None
                            start_time_str = embedded_race.get('start_time') or race_detail.get('start_time') or race_detail.get('off_time')
                            if start_time_str:
                                try:
                                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                                except:
                                    pass

                            # Parse distance (remove 'm' suffix)
                            distance_str = race_detail.get('distance') or '1200m'
                            distance = int(distance_str.replace('m', '').replace('M', ''))

                            # Parse runners
                            runners = []
                            for runner_data in race_detail.get('runners', []):
                                # Skip scratched horses
                                if runner_data.get('scratched', False):
                                    continue

                                # Extract price from odds array or SP
                                price = 5.0  # Default

                                # First try to get from odds array
                                odds_array = runner_data.get('odds', [])
                                if odds_array:
                                    # Use first bookmaker odds
                                    price = float(odds_array[0].get('win_odds', 5.0))

                                # Fallback to SP if no odds array
                                if price == 5.0 and runner_data.get('sp'):
                                    price = float(runner_data.get('sp', 5.0))

                                horse_name = runner_data.get('horse', 'Unknown')

                                # Parse form string
                                form_string = runner_data.get('form') or ''
                                last_starts = self._parse_form_string(form_string)

                                # Parse weight (remove 'kg' suffix)
                                weight_str = runner_data.get('weight') or '0kg'
                                try:
                                    weight = float(str(weight_str).replace('kg', '').replace('KG', ''))
                                except (ValueError, AttributeError):
                                    weight = 0.0

                                # Get saddlecloth and barrier with safe defaults
                                saddlecloth = runner_data.get('number') or runner_data.get('cloth') or 0
                                try:
                                    saddlecloth = int(saddlecloth)
                                except (ValueError, TypeError):
                                    saddlecloth = 0

                                barrier = runner_data.get('draw') or runner_data.get('barrier') or saddlecloth
                                try:
                                    barrier = int(barrier)
                                except (ValueError, TypeError):
                                    barrier = saddlecloth

                                # Build runner object
                                runner = Runner(
                                    saddlecloth=saddlecloth,
                                    name=horse_name,
                                    price=price,
                                    barrier=barrier,
                                    jockey=runner_data.get('jockey', ''),
                                    trainer=runner_data.get('trainer', ''),
                                    weight=weight,
                                    last_starts=last_starts,
                                    recent_form=form_string,
                                    class_rating=self._derive_class_rating_premium(runner_data),
                                    speed_rating=self._derive_speed_rating_premium(runner_data)
                                )
                                runners.append(runner)

                            if not runners:
                                print(f"    ⚠️ R{race_number}: No runners found")
                                continue

                            # Create race object
                            race = Race(
                                track_name=track_name,
                                race_number=race_number,
                                distance=distance,
                                surface=race_detail.get('going') or 'Good',
                                grade=race_detail.get('class') or 'Unknown',
                                runners=runners,
                                start_time=start_time
                            )

                            races.append(race)
                            print(f"    ✓ R{race_number}: {len(runners)} runners")

                    except (ValueError, KeyError, TypeError) as e:
                        print(f"    ⚠️  Error parsing race {race_number}: {e}")
                        continue

            except (ValueError, KeyError, TypeError) as e:
                print(f"⚠️  Error parsing meet {track_name}: {e}")
                continue

        return races

    def parse_racecards_to_races(self, racecards_data: Dict) -> List['Race']:
        """Parse API racecard data into Race objects"""
        races = []

        if not racecards_data or 'racecards' not in racecards_data:
            return races

        # Group racecards by course and assign race numbers
        race_num_counter = {}

        for race_data in racecards_data.get('racecards', []):
            try:
                # Skip trials and jump outs (practice races, not official betting races)
                if race_data.get('is_trial') or race_data.get('is_jump_out'):
                    continue

                course = race_data.get('course', 'Unknown')

                # Assign race number based on time order per course
                if course not in race_num_counter:
                    race_num_counter[course] = 1
                else:
                    race_num_counter[course] += 1

                race_number = race_num_counter[course]

                # Parse runners
                runners = []
                for runner_data in race_data.get('runners', []):
                    # Parse form string to last_starts list
                    form_string = runner_data.get('form', '')
                    last_starts = self._parse_form_string(form_string)

                    # Extract jockey name (remove claim weight)
                    jockey_full = runner_data.get('jockey', '')
                    jockey = jockey_full.split('(')[0].strip()

                    # Convert lbs to kg for weight
                    lbs = float(runner_data.get('lbs', 0))
                    weight_kg = lbs * 0.453592 if lbs > 0 else 0.0

                    # Get barrier/draw (use number if draw is 0)
                    draw = int(runner_data.get('draw', 0))
                    barrier = draw if draw > 0 else int(runner_data.get('number', 0))

                    # Get horse name
                    horse_name = runner_data.get('horse', 'Unknown')

                    # Get price from API (free tier has limited odds data)
                    price = 5.0  # Default fallback

                    runner = Runner(
                        saddlecloth=int(runner_data.get('number', 0)),
                        name=horse_name,
                        price=price,
                        barrier=barrier,
                        jockey=jockey,
                        trainer=runner_data.get('trainer', ''),
                        weight=weight_kg,
                        last_starts=last_starts,
                        class_rating=self._derive_class_rating(runner_data),
                        speed_rating=self._derive_speed_rating(runner_data)
                    )
                    runners.append(runner)

                # Convert distance from furlongs to meters (1 furlong = 201.168 meters)
                distance_f = float(race_data.get('distance_f', 10))
                distance_m = int(distance_f * 201.168)

                # Create race object
                race = Race(
                    track_name=course,
                    race_number=race_number,
                    distance=distance_m,
                    surface=race_data.get('surface', 'Turf'),
                    grade=race_data.get('race_class', 'Unknown'),
                    runners=runners
                )

                if race.runners:  # Only add races with runners
                    races.append(race)

            except (ValueError, KeyError) as e:
                print(f"Error parsing race: {e}")
                continue

        return races

    def _parse_form_string(self, form_string: str) -> List[int]:
        """Parse form string like '1-2-3-x' into [1, 2, 3, 0]"""
        if not form_string:
            return []

        last_starts = []
        for char in form_string.replace('-', ''):
            if char.isdigit():
                last_starts.append(int(char))
            elif char.lower() == 'x':
                last_starts.append(0)  # DNF

        return last_starts[:5]  # Keep last 5 starts

    def _derive_class_rating(self, runner_data: Dict) -> int:
        """Derive class rating from runner data (0-100)"""
        # Use OFR (Official Rating) if available
        ofr = runner_data.get('ofr', '')

        try:
            if ofr and ofr.replace('-', '').isdigit():
                rating = int(ofr)
                # Normalize to 0-100 (typical ratings are 0-140)
                return min(100, int((rating / 140) * 100))
        except (ValueError, AttributeError):
            pass

        # Fallback: estimate from form
        return 50  # Default average rating

    def _derive_speed_rating(self, runner_data: Dict) -> int:
        """Derive speed rating from runner data (0-100)"""
        # Use speed figure if available
        speed = runner_data.get('speed_rating', runner_data.get('speed_figure', 0))

        if speed > 0:
            return min(100, speed)

        # Fallback: estimate from class rating
        return self._derive_class_rating(runner_data)

    def _derive_class_rating_premium(self, runner_data: Dict) -> int:
        """
        Derive class rating from Premium Australia API runner data (0-100)
        Uses comprehensive stats for better accuracy
        """
        rating = 50  # Start at average

        # Use rating field if available
        if runner_data.get('rating'):
            try:
                official_rating = int(runner_data['rating'])
                # Normalize to 0-100 (typical ratings are 0-140)
                rating = min(100, int((official_rating / 140) * 100))
                return rating
            except (ValueError, TypeError):
                pass

        # Use stats to estimate class
        stats = runner_data.get('stats', {})

        # Career win/place percentage indicates class
        career_win_pct = stats.get('career_win_percent')
        career_place_pct = stats.get('career_place_percent')

        if career_win_pct is not None:
            try:
                win_pct = float(career_win_pct)
                # 20%+ win rate = high class, 10% = average, <5% = low class
                rating = max(30, min(90, 30 + int(win_pct * 3)))
            except (ValueError, TypeError):
                pass
        elif career_place_pct is not None:
            try:
                place_pct = float(career_place_pct)
                # 50%+ place rate = high class
                rating = max(30, min(85, 30 + int(place_pct * 1.5)))
            except (ValueError, TypeError):
                pass

        # Boost for course/distance winners
        course_dist_stats = stats.get('course_distance_stats', {})
        if course_dist_stats:
            total = int(course_dist_stats.get('total', 0))
            firsts = int(course_dist_stats.get('first', 0))
            if total > 0 and firsts > 0:
                rating += 10  # Proven at course & distance

        return max(20, min(100, rating))

    def _derive_speed_rating_premium(self, runner_data: Dict) -> int:
        """
        Derive speed rating from Premium Australia API runner data (0-100)
        Uses stats and form to estimate speed ability
        """
        rating = 50  # Start at average

        # Check if horse has won recently
        stats = runner_data.get('stats', {})
        last_won = stats.get('last_won')

        if last_won:
            # Recent winners get speed boost
            rating += 15

        # Check distance stats
        dist_stats = stats.get('distance_stats', {})
        if dist_stats:
            total = int(dist_stats.get('total', 0))
            firsts = int(dist_stats.get('first', 0))

            if total > 0:
                win_rate = firsts / total
                # Good distance record indicates speed
                rating += int(win_rate * 30)

        # Parse form for recent wins (1st place)
        form = runner_data.get('form', '')
        if form:
            recent_wins = form[:5].count('1')  # Wins in last 5 starts
            rating += recent_wins * 5

        return max(20, min(100, rating))


class HorseRacingAnalyst:
    """
    PRODUCTION HORSE RACING ANALYST
    RSI-based selection system with win percentages
    Deterministic and simplified
    """

    # RSI THRESHOLDS BY ODDS RANGE (EDGE bet criteria)
    # Short-mid odds: no RSI floor (Kelly handles filtering)
    # Longshots ($7+): require higher RSI + top market rank to qualify
    RSI_THRESHOLDS = {
        (1.80, 2.51): 0,
        (2.51, 4.01): 0,
        (4.01, 7.01): 0,
        (7.01, 12.01): 45,
        (12.01, 15.01): 55
    }

    # MARKET RANK LIMITS - tightened for longshots
    # Longshots must be near the top of the market to qualify
    MARKET_RANK_LIMITS = {
        (1.80, 2.51): 3,
        (2.51, 4.01): 3,
        (4.01, 7.01): 3,
        (7.01, 12.01): 3,
        (12.01, 15.01): 3
    }

    def __init__(self):
        self.analysis_cache = {}

    def _get_minimum_rsi(self, odds: float) -> int:
        """Get minimum RSI required for given odds to be Tracked"""
        for (min_odds, max_odds), min_rsi in self.RSI_THRESHOLDS.items():
            if min_odds <= odds < max_odds:
                return min_rsi
        return 999  # Out of range

    def _get_market_rank_limit(self, odds: float) -> int:
        """Get maximum market rank allowed for given odds to be Tracked"""
        for (min_odds, max_odds), max_rank in self.MARKET_RANK_LIMITS.items():
            if min_odds <= odds < max_odds:
                return max_rank
        return 0  # Out of range

    def _calculate_market_rank(self, runner: Runner, race: Race) -> int:
        """Calculate horse's market rank (1 = favorite)"""
        sorted_runners = sorted(race.runners, key=lambda r: r.price)
        for rank, r in enumerate(sorted_runners, 1):
            if r.name == runner.name:
                return rank
        return 999

    def _is_tracked(self, runner: Runner, race: Race, rsi: int, win_pct: float) -> bool:
        """
        Check if selection qualifies as a bet
        Applies RSI thresholds, market rank limits, and odds cap for longshots
        """
        # Must have valid odds ($1.80 minimum, $15 max)
        if runner.price < 1.80:
            return False
        if runner.price > 15.0:
            return False

        # Check RSI threshold for this odds range
        min_rsi = self._get_minimum_rsi(runner.price)
        if rsi < min_rsi:
            return False

        # Check market rank limit for this odds range
        market_rank = self._calculate_market_rank(runner, race)
        max_rank = self._get_market_rank_limit(runner.price)
        if market_rank > max_rank:
            return False

        return True

    def _should_bet(self, rsi: int) -> bool:
        """Check if RSI meets minimum threshold to place any bet"""
        # Always bet on highest RSI horse in each race
        return True

    def analyze_program(self, races: List[Race], minutes_before: int = 3) -> str:
        """
        Main entry point for analysis
        Outputs races starting within specified minutes
        """
        now = datetime.now(timezone.utc)

        # Filter valid races (must have runners, basic data, real odds, and start within time window)
        valid_races = []
        for r in races:
            if not r.is_valid():
                continue

            # Check if race has real odds (not all defaulting to $5.00)
            prices = [runner.price for runner in r.runners]
            unique_prices = set(prices)
            if unique_prices == {5.0}:
                continue

            # Check if race starts within the time window
            if r.start_time:
                time_until_start = (r.start_time - now).total_seconds() / 60  # minutes
                # Only include races starting within 0-3 minutes
                if time_until_start < 0 or time_until_start > minutes_before:
                    continue
            else:
                # No start time - skip
                continue

            valid_races.append(r)

        if len(valid_races) == 0:
            return ""  # No valid races

        # Sort by start time (soonest first)
        valid_races.sort(key=lambda r: r.start_time if r.start_time else datetime.max.replace(tzinfo=timezone.utc))

        # Output all races in new format
        output_lines = []

        for race in valid_races:
            # Get top selection based on RSI
            selection = self._get_top_selection(race)

            if not selection:
                continue  # Skip if no selection possible

            # Calculate RSI and Win %
            rsi = self._calculate_rsi(selection, race)
            win_pct = self._calculate_win_percentage(selection, race, rsi)

            # Calculate Units (Kelly Criterion based)
            units = self._calculate_units(selection, win_pct, rsi)

            # Check if this is a Tracked bet (meets backtested criteria)
            is_tracked = self._is_tracked(selection, race, rsi, win_pct)

            # Format output (4 lines per race)
            # Tracked bets are marked with **bold** formatting
            if is_tracked:
                # TRACKED BET - Bold formatting
                line1 = f"**{race.track_name} - {race.race_number}**"
                line2 = f"**{race.distance}m - {race.surface}**"
                line3 = f"**{race.track_name} {race.race_number} | {selection.saddlecloth} {selection.name}**"
                line4 = f"**${selection.price:.2f} {units}u {int(rsi)}%** EDGE"
            else:
                # Regular bet - no bold
                line1 = f"{race.track_name} - {race.race_number}"
                line2 = f"{race.distance}m - {race.surface}"
                line3 = f"{race.track_name} {race.race_number} | {selection.saddlecloth} {selection.name}"
                line4 = f"${selection.price:.2f} {units}u {int(rsi)}%"

            # Add all lines for this race
            output_lines.append(line1)
            output_lines.append(line2)
            output_lines.append(line3)
            output_lines.append(line4)
            output_lines.append("")  # Blank line between races

        return "\n".join(output_lines)

    def _calculate_units(self, runner: Runner, win_pct: float, rsi: int) -> float:
        """
        Calculate betting units using 1/2 Kelly Criterion

        Kelly % = (bp - q) / b * 0.5
        where:
        - b = decimal_odds - 1
        - p = win probability (win_pct / 100)
        - q = 1 - p (loss probability)
        - 0.5 = 1/2 Kelly multiplier

        Assumes 100 unit bankroll (1% of bankroll = 1 unit)
        """
        odds = runner.price

        # Convert win percentage to probability
        p = win_pct / 100.0
        q = 1.0 - p

        # Calculate Kelly fraction
        b = odds - 1.0

        # Avoid division by zero for odds of 1.0 or less (shouldn't happen in practice)
        if b <= 0:
            return 0.0

        # Kelly formula: (bp - q) / b
        kelly_fraction = (b * p - q) / b

        # Apply 1/2 Kelly multiplier
        half_kelly = kelly_fraction * 0.5

        # If Kelly is negative, there's no edge - don't bet
        if half_kelly <= 0:
            return 0.0

        # Convert to units (assuming 100 unit bankroll)
        # 1% of bankroll = 1 unit, so multiply by 100
        units = half_kelly * 100

        # Apply safety bounds with odds-based scaling
        # Aggressive on strong favorites, conservative on longshots
        if odds < 4.0:
            max_units = 4.0
        elif odds < 7.0:
            max_units = 2.5
        elif odds < 10.0:
            max_units = 1.5
        elif odds < 15.0:
            max_units = 1.0
        else:
            max_units = 0.5

        units = max(units, 0.5)  # Minimum 0.5 units if positive edge
        units = min(units, max_units)  # Cap based on odds range

        return round(units, 2)

    # ========================================
    # SELECTION METHODS
    # ========================================

    def _get_top_selection(self, race: Race) -> Optional[Runner]:
        """
        Get single best selection for a race based on RSI
        Returns runner or None
        """
        if not race.runners:
            return None

        # Calculate RSI for all runners
        scored = []
        for runner in race.runners:
            rsi = self._calculate_rsi(runner, race)
            scored.append({
                'runner': runner,
                'rsi': rsi
            })

        # Sort by RSI (deterministic tie-break: lowest saddlecloth)
        scored.sort(key=lambda x: (-x['rsi'], x['runner'].saddlecloth))

        # Return top runner
        return scored[0]['runner']


    # ========================================
    # SCORING & ASSESSMENT FUNCTIONS
    # ========================================

    def _calculate_rsi(self, runner: Runner, race: Race) -> int:
        """
        Calculate RSI (Racing Strength Index) - 1 to 100

        Weights (optimized for ROI):
        - Horse Form & Ability: 35%
        - Market Intelligence: 15%
        - Track/Distance/Going: 15%
        - Class & Map: 15%
        - Trainer: 12%
        - Jockey: 8%
        """
        rsi = 0

        # ========================================
        # 1. HORSE FORM & ABILITY (35 points max)
        # ========================================
        form_score = 0

        # Recent finishing positions vs class (13 points)
        if runner.last_starts and len(runner.last_starts) > 0:
            recent = runner.last_starts[:3]

            # Win bonus (5 points per win in last 3)
            wins = sum(1 for pos in recent if pos == 1)
            form_score += wins * 5

            # Place bonus (2 points per place in last 3)
            places = sum(1 for pos in recent if 2 <= pos <= 3)
            form_score += places * 2

            # Consistency (low variance = good)
            if len(recent) >= 2:
                try:
                    avg_pos = statistics.mean(recent)
                    if avg_pos <= 3:
                        form_score += 1
                except:
                    pass

        # Speed figures / time ratings (13 points)
        speed_component = min(13, (runner.speed_rating / 100) * 13)
        form_score += speed_component

        # Margin beaten & closing splits (9 points) - use improvement trend
        if runner.last_starts and len(runner.last_starts) >= 2:
            if runner.last_starts[0] < runner.last_starts[1]:
                form_score += 5  # Improving
            elif runner.last_starts[0] == runner.last_starts[1]:
                form_score += 2  # Consistent
            # Recent win gets bonus
            if runner.last_starts[0] == 1:
                form_score += 4

        form_score = min(35, form_score)
        rsi += int(form_score)

        # ========================================
        # 2. TRAINER (12 points max)
        # ========================================
        trainer_score = 0

        # Trainer strike rate overall (5 points) - base score
        trainer_score += 3  # Default baseline

        # Trainer at track/distance (4 points) - use class rating as proxy
        if runner.class_rating >= 70:
            trainer_score += 4
        elif runner.class_rating >= 50:
            trainer_score += 2

        # Trainer + jockey combo (3 points) - bonus if both present
        if runner.trainer and runner.jockey:
            trainer_score += 3

        trainer_score = min(12, trainer_score)
        rsi += int(trainer_score)

        # ========================================
        # 3. JOCKEY (8 points max)
        # ========================================
        jockey_score = 0

        # Jockey win/place rate (4 points)
        if runner.jockey:
            jockey_score += 3  # Has known jockey

        # Jockey at track/distance (4 points) - use speed rating as proxy
        if runner.speed_rating >= 70:
            jockey_score += 4
        elif runner.speed_rating >= 50:
            jockey_score += 2

        jockey_score = min(8, jockey_score)
        rsi += int(jockey_score)

        # ========================================
        # 4. TRACK, DISTANCE & CONDITIONS (15 points max)
        # ========================================
        track_score = 0

        # Track suitability (5 points)
        track_score += 3  # Base track score

        # Distance suitability (5 points) - use form as proxy
        if runner.last_starts and len(runner.last_starts) > 0:
            if runner.last_starts[0] <= 3:
                track_score += 5  # Recent good run = distance suited
            elif runner.last_starts[0] <= 5:
                track_score += 3

        # Going/surface (5 points)
        if race.surface.lower() in ['good', 'turf', 'firm']:
            track_score += 4  # Standard conditions
        else:
            track_score += 2  # Wet/heavy/synthetic

        track_score = min(15, track_score)
        rsi += int(track_score)

        # ========================================
        # 5. CLASS & MAP FACTORS (15 points max)
        # ========================================
        class_map_score = 0

        # Class movement up/down (6 points)
        if race.runners:
            avg_class = statistics.mean([r.class_rating for r in race.runners])
            if runner.class_rating > avg_class * 1.15:
                class_map_score += 6  # Class drop / advantage
            elif runner.class_rating > avg_class:
                class_map_score += 3

        # Barrier + expected map position (6 points)
        if runner.barrier <= 4:
            class_map_score += 6  # Inside barrier advantage
        elif runner.barrier <= 8:
            class_map_score += 4  # Mid barrier OK
        elif runner.barrier <= 12:
            class_map_score += 2  # Wide but manageable
        else:
            class_map_score += 0  # Very wide

        # Field strength vs last start (3 points)
        if race.runners and len(race.runners) <= 10:
            class_map_score += 2  # Smaller field = less traffic
        elif race.runners and len(race.runners) <= 14:
            class_map_score += 1

        class_map_score = min(15, class_map_score)
        rsi += int(class_map_score)

        # ========================================
        # 6. MARKET INTELLIGENCE (15 points max)
        # ========================================
        market_score = 0

        # Market rank (9 points) - market is highly predictive
        if race.runners:
            sorted_by_price = sorted(race.runners, key=lambda r: r.price)
            market_rank = next((i for i, r in enumerate(sorted_by_price, 1) if r.name == runner.name), 99)

            if market_rank == 1:
                market_score += 9  # Favourite
            elif market_rank == 2:
                market_score += 7
            elif market_rank == 3:
                market_score += 5
            elif market_rank <= 5:
                market_score += 3

        # Price confidence (6 points) - shorter prices = market confidence
        if runner.price <= 2.5:
            market_score += 6  # Very short price = high confidence
        elif runner.price <= 4.0:
            market_score += 5
        elif runner.price <= 6.0:
            market_score += 4
        elif runner.price <= 10.0:
            market_score += 2
        elif runner.price <= 15.0:
            market_score += 1

        market_score = min(15, market_score)
        rsi += int(market_score)

        # Ensure RSI is between 1 and 100
        return max(1, min(100, rsi))

    def _calculate_win_percentage(self, runner: Runner, race: Race, rsi: int) -> float:
        """
        Calculate win probability percentage
        Based on RSI, price, and field strength
        """
        # 1. Base probability from market price
        if runner.price > 0:
            implied_prob = (1 / runner.price) * 100
        else:
            implied_prob = 5.0

        # 2. Calculate all RSI scores for the field
        all_rsi = []
        for r in race.runners:
            r_rsi = self._calculate_rsi(r, race)
            all_rsi.append(r_rsi)

        # 3. RSI-based probability using softmax-like approach
        if all_rsi:
            # Runner's RSI relative to field
            total_rsi = sum(all_rsi)
            if total_rsi > 0:
                rsi_prob = (rsi / total_rsi) * 100
            else:
                rsi_prob = 100 / len(race.runners)
        else:
            rsi_prob = 100 / len(race.runners)

        # 4. Form consistency adjustment
        form_bonus = 0
        if runner.last_starts and len(runner.last_starts) >= 3:
            try:
                std_dev = statistics.stdev(runner.last_starts[:3])
                if std_dev < 1.5:  # Very consistent
                    form_bonus = 2.0
                elif std_dev < 2.5:  # Reasonably consistent
                    form_bonus = 1.0
            except:
                pass

        # 5. Combine probabilities (weighted average)
        # 50% RSI, 50% market price (market is efficient)
        final_prob = (rsi_prob * 0.5) + (implied_prob * 0.5) + form_bonus

        # 6. Normalize to realistic range
        # Allow higher cap for strong favourites, lower cap for outsiders
        if runner.price <= 2.5:
            max_prob = 55.0  # Strong favourites can have higher win rates
        elif runner.price <= 4.0:
            max_prob = 45.0
        elif runner.price <= 7.0:
            max_prob = 35.0
        else:
            max_prob = 25.0  # Longshots capped lower

        final_prob = max(5.0, min(max_prob, final_prob))

        return round(final_prob, 1)





# ========================================
# FACTORY FUNCTIONS
# ========================================

def create_analyst() -> HorseRacingAnalyst:
    """Factory function to create analyst instance"""
    return HorseRacingAnalyst()


def auto_settle_bets(api_client: 'RacingAPIClient', bet_tracker: 'BetTracker',
                     discord: 'DiscordNotifier' = None) -> int:
    """
    Automatically settle pending bets using race results from the API
    Returns number of bets settled
    """
    pending = bet_tracker.get_pending_bets()
    print(f"🔄 Checking {len(pending)} pending bet(s) for results...")
    if not pending:
        return 0

    # Only check bets that started more than 10 minutes ago (race should be finished)
    now = datetime.now(timezone.utc)
    settled_count = 0

    for i, bet in enumerate(pending):
        # Add delay between API calls to avoid rate limiting
        if i > 0:
            time.sleep(2)  # 2 second delay between checks

        try:
            track = bet.get("track", "")
            race_num = bet.get("race_num", 0)
            horse_name = bet.get("horse_name", "")
            race_time_str = bet.get("race_time", "")

            print(f"   📋 Bet: {track} R{race_num} - {horse_name}, race_time={race_time_str}")

            if not race_time_str:
                print(f"   ⚠️ No race_time set for this bet - settling as unknown")
                continue

            race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
            minutes_since_start = (now - race_time).total_seconds() / 60

            print(f"   ⏱️ Minutes since start: {minutes_since_start:.1f}")

            # Only check races that started 10+ minutes ago
            if minutes_since_start < 10:
                print(f"   ⏳ Race too recent, waiting...")
                continue

            print(f"🔍 Checking result for {track} R{race_num} ({horse_name})...")

            # Get race result from API
            result = api_client.get_race_result(track, race_num)

            if not result:
                print(f"   ⚠️ No result found for {track} R{race_num}")
            else:
                print(f"   ✓ Found result: {result.get('positions', {})}")

            if result and result.get("positions"):
                positions = result.get("positions", {})

                # Normalize horse name for matching
                def normalize_name(name):
                    """Remove common suffixes and special chars for better matching"""
                    import re
                    name = name.lower().strip()
                    # Remove country codes in parentheses
                    name = re.sub(r'\s*\([a-z]{2,3}\)\s*$', '', name, flags=re.IGNORECASE)
                    # Remove extra whitespace and special chars
                    name = re.sub(r'[^\w\s]', '', name)
                    name = re.sub(r'\s+', ' ', name)
                    return name.strip()

                horse_normalized = normalize_name(horse_name)

                # Debug: Show what we're looking for
                print(f"   🔎 Looking for: '{horse_name}' (normalized: '{horse_normalized}')")
                print(f"   📋 Available horses in results: {list(positions.keys())}")

                # Find our horse's position with improved matching
                position = None
                matched_name = None
                for name, pos in positions.items():
                    name_normalized = normalize_name(name)

                    # Try multiple matching strategies
                    if (horse_normalized == name_normalized or
                        horse_normalized in name_normalized or
                        name_normalized in horse_normalized or
                        # Also try exact match on original names
                        horse_name.lower().strip() == name.lower().strip()):
                        position = pos
                        matched_name = name
                        print(f"   ✓ Match found: '{name}' = position {pos}")
                        break

                if position:
                    # Settle the bet
                    if bet_tracker.settle_bet_by_horse(track, race_num, horse_name, position):
                        settled_count += 1
                        is_win = position == 1
                        emoji = "🎉🏆" if is_win else "❌"
                        result_text = "WON - SEND SLIPS INTO WINS!" if is_win else f"#{position}"

                        print(f"{emoji} Settled: {track} R{race_num} - {horse_name} {result_text}")

                        # Notify Discord
                        if discord and is_win:
                            payout = bet.get("units", 0) * bet.get("price", 0)
                            profit = payout - bet.get("units", 0)
                            discord.send_message(
                                f"🎉🏆 **WINNER!** 🏆🎉\n"
                                f"**{horse_name}** @ ${bet.get('price', 0):.2f} - {track} R{race_num}\n"
                                f"💰 Payout: {payout:.1f}u (+{profit:.1f}u profit)\n"
                                f"🎊 **SEND SLIPS INTO WINS!** 🎊"
                            )
                else:
                    # Horse not in results - likely scratched
                    # Only mark as scratched if race finished 60+ mins ago (give MORE time for results)
                    if minutes_since_start > 60:
                        print(f"   ⚠️ WARNING: Could not match '{horse_name}' in results after 60 mins")
                        print(f"   ⚠️ Marking as scratched. If this is incorrect, check name matching!")
                        if bet_tracker.settle_as_scratched(track, race_num, horse_name):
                            settled_count += 1
                            print(f"🚫 SCRATCHED: {track} R{race_num} - {horse_name} (not in results)")
                            if discord:
                                discord.send_message(
                                    f"🚫 **SCRATCHED** {track} R{race_num}\n"
                                    f"**{horse_name}** - Stake refunded"
                                )
                    else:
                        print(f"   ⏳ Horse not matched yet, waiting longer (need 60+ mins)...")

        except (ValueError, TypeError) as e:
            print(f"   ⚠️ Error processing bet: {e}")
            continue

    return settled_count




# ========================================
# MAIN EXECUTION
# ========================================

def main():
    """Main entry point - continuously monitor races and output 3 mins before start"""
    # Load environment variables
    load_dotenv()

    # Get API credentials from .env
    username = os.getenv('RACING_API_USERNAME')
    password = os.getenv('RACING_API_PASSWORD')
    discord_token = os.getenv('DISCORD_TOKEN')
    discord_channel = os.getenv('DISCORD_CHANNEL_ID')

    if not username or not password:
        print("Error: RACING_API_USERNAME and RACING_API_PASSWORD must be set in .env file")
        return

    print("=" * 60)
    print("HORSE TIPPER - Live Race Monitor")
    print("EDGE BETS ONLY - High confidence selections")
    print("Outputs selections 3 minutes before race start")
    if discord_token and discord_channel:
        print("✓ Discord bot enabled")
    else:
        print("⚠ No DISCORD_TOKEN/DISCORD_CHANNEL_ID set - console output only")
    print("=" * 60)

    # Initialize API client, Discord, and bet tracker
    api_client = RacingAPIClient(username, password)
    analyst = create_analyst()
    discord = DiscordNotifier(discord_token, discord_channel) if discord_token and discord_channel else None
    bet_tracker = BetTracker()

    # Start Discord command handler
    command_handler = None
    if discord:
        command_handler = DiscordCommandHandler(discord, bet_tracker)
        command_handler.start()

    # Track races we've already output to avoid duplicates
    output_races = set()

    print("\nFetching initial race data...")

    # Do initial fetch with verbose output
    australia_data = api_client.get_australia_meets()
    if australia_data and 'meets' in australia_data:
        races = api_client.parse_australia_to_races(australia_data)
        print(f"\n✓ Loaded {len(races)} races")
    else:
        races = []
        print("No races found")

    print("\nMonitoring for races starting soon... (Ctrl+C to stop)\n")

    # Track last fetch time and last settlement check
    last_fetch_time = time.time()
    last_settlement_check = time.time()

    while True:
        try:
            # Check for results and settle bets every 5 minutes (avoid rate limits)
            if time.time() - last_settlement_check > 300:
                settled = auto_settle_bets(api_client, bet_tracker, discord)
                if settled > 0:
                    print(f"✓ Auto-settled {settled} bet(s)")
                last_settlement_check = time.time()

            # Silently refresh race data every 2 minutes
            if time.time() - last_fetch_time > 120:
                australia_data = api_client.get_australia_meets()
                if australia_data and 'meets' in australia_data:
                    # Temporarily suppress print during refresh
                    old_stdout = sys.stdout
                    sys.stdout = io.StringIO()
                    races = api_client.parse_australia_to_races(australia_data)
                    sys.stdout = old_stdout
                last_fetch_time = time.time()

            if races:
                # Filter races starting within 3 minutes
                now = datetime.now(timezone.utc)

                for race in races:
                    if not race.start_time:
                        continue

                    # Create unique race key
                    race_key = f"{race.track_name}_R{race.race_number}_{race.start_time.isoformat()}"

                    # Skip if already output
                    if race_key in output_races:
                        continue

                    # Check time until start
                    time_until_start = (race.start_time - now).total_seconds() / 60

                    # Output if within 3 minutes
                    if 0 <= time_until_start <= 3:
                        # Get local time
                        local_time = race.start_time.astimezone(AEDT)
                        race_time_str = local_time.strftime('%H:%M')

                        # ========================================
                        # EDGE BET (RSI-based selection)
                        # ========================================
                        selection = analyst._get_top_selection(race)
                        if not selection:
                            continue

                        # Calculate metrics
                        rsi = analyst._calculate_rsi(selection, race)
                        win_pct = analyst._calculate_win_percentage(selection, race, rsi)
                        units = analyst._calculate_units(selection, win_pct, rsi)
                        is_tracked = analyst._is_tracked(selection, race, rsi, win_pct)
                        market_rank = analyst._calculate_market_rank(selection, race)

                        # ONLY post EDGE betsh
                        if not is_tracked:
                            output_races.add(race_key)
                            continue

                        # Skip if Kelly returns 0 units (no edge)
                        if units <= 0:
                            output_races.add(race_key)
                            continue

                        # Record the bet
                        bet_tracker.record_bet(
                            track=race.track_name,
                            race_num=race.race_number,
                            horse_name=selection.name,
                            horse_num=selection.saddlecloth,
                            price=selection.price,
                            units=units,
                            rsi=rsi,
                            is_tracked=is_tracked,
                            race_time=race.start_time,
                            market_rank=market_rank
                        )

                        # Send to Discord
                        if discord:
                            discord.send_tip(
                                race_time=race_time_str,
                                track=race.track_name,
                                race_num=race.race_number,
                                distance=race.distance,
                                surface=race.surface,
                                horse_num=selection.saddlecloth,
                                horse_name=selection.name,
                                price=selection.price,
                                units=units,
                                rsi=rsi,
                                is_tracked=is_tracked,
                                market_rank=market_rank
                            )

                        # Print to console
                        bet_type = "🔥 BEST BET" if market_rank == 1 else "📊 EDGE BET"
                        print(f"\n⏰ {race_time_str} | {race.track_name} R{race.race_number} [{bet_type}]")
                        print(f"   {selection.saddlecloth}. {selection.name} @ ${selection.price:.2f}")
                        print(f"   {units}u | RSI {rsi}% | Market Rank: {market_rank}")

                        output_races.add(race_key)

            # Wait 30 seconds before next check
            time.sleep(30)

        except KeyboardInterrupt:
            print("\n\nStopping monitor...")
            if command_handler:
                command_handler.stop()
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(30)

    # Ensure command handler is stopped
    if command_handler:
        command_handler.stop()

if __name__ == "__main__":
    print("=" * 60)
    print("🏇 HORSE RACING AI - STARTING UP")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Current time: {datetime.now(AEDT).strftime('%Y-%m-%d %H:%M:%S AEDT')}")
    print()

    try:
        main()
    except Exception as e:
        print(f"💥 FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise
    