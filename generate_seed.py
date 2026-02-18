#!/usr/bin/env python3
"""
Generate backtest_seed.json for NEX SNIPE + NEX BET systems.
Uses 32-day PF cache (Jan 18 – Feb 18 2026).
Output format matches BetTracker record_bet() schema.

Run: python3 generate_seed.py
"""

import json
import os
from datetime import datetime, timezone, timedelta

PF_CACHE = os.path.expanduser("~/pf_cache")
AEDT = timezone(timedelta(hours=11))

# ── Filters (mirror horse_analyst.py constants) ────────────────────────────
SN_MIN_PRICE  = 2.50;  SN_MAX_PRICE  = 8.00
SN_MAX_RANK   = 2;     SN_MIN_SCORE  = 80
SN_MAX_TR     = 3;     SN_MAX_SETTLE = 3
SN_PACE       = {"op"};SN_MIN_WIN    = 5.0;  SN_MAX_CC = 0.0

HV_MIN_PRICE  = 2.50;  HV_MAX_PRICE  = 8.00
HV_MAX_RANK   = 5;     HV_MIN_SCORE  = 70
HV_MAX_TR     = 99;    HV_MAX_SETTLE = 3
HV_PACE       = {"op"};HV_MIN_WIN    = 5.0


def norm_style(raw: str) -> str:
    s = (raw or "").strip().lower()
    return s.replace("/", "_") if "/" in s else s


def is_snipe(r) -> bool:
    price = r.get("priceSP") or 0
    if not (SN_MIN_PRICE <= price <= SN_MAX_PRICE):  return False
    rank = r.get("pfaiRank") or 99
    if rank > SN_MAX_RANK:                           return False
    score = r.get("pfaiScore") or 0
    if score < SN_MIN_SCORE:                         return False
    tr = r.get("timeRank") or 99
    if tr > SN_MAX_TR:                               return False
    if not r.get("isReliable"):                      return False
    style = norm_style(r.get("runStyle", ""))
    if style not in SN_PACE:                         return False
    ps = r.get("predictedSettle") or 99
    if ps > SN_MAX_SETTLE:                           return False
    win_pct = float(r.get("winPct") or 0)
    if win_pct < SN_MIN_WIN:                         return False
    cc = r.get("classChange")
    if cc is None or float(cc) > SN_MAX_CC:          return False
    return True


def is_nex_bet(r) -> bool:
    price = r.get("priceSP") or 0
    if not (HV_MIN_PRICE <= price <= HV_MAX_PRICE):  return False
    rank = r.get("pfaiRank") or 99
    if rank > HV_MAX_RANK:                           return False
    score = r.get("pfaiScore") or 0
    if score < HV_MIN_SCORE:                         return False
    tr = r.get("timeRank") or 99
    if tr > HV_MAX_TR:                               return False
    if not r.get("isReliable"):                      return False
    style = norm_style(r.get("runStyle", ""))
    if style not in HV_PACE:                         return False
    ps = r.get("predictedSettle") or 99
    if ps > HV_MAX_SETTLE:                           return False
    win_pct = float(r.get("winPct") or 0)
    if win_pct < HV_MIN_WIN:                         return False
    return True


def confidence(r, mode: str) -> float:
    pf_score   = float(r.get("pfaiScore") or 0)
    pf_rank    = int(r.get("pfaiRank") or 99)
    pred_settle= int(r.get("predictedSettle") or 3)
    min_score  = SN_MIN_SCORE if mode == "SNIPER" else HV_MIN_SCORE
    max_rank   = SN_MAX_RANK  if mode == "SNIPER" else HV_MAX_RANK
    max_settle = SN_MAX_SETTLE

    score_range = max(1, 100 - min_score)
    sc  = min(1.0, max(0.0, (pf_score - min_score) / score_range))
    rk  = max(0.0, 1.0 - (pf_rank - 1) / max(1, max_rank))
    ps  = max(0.0, (max_settle + 1 - pred_settle) / max_settle)
    raw = 0.40 * sc + 0.35 * rk + 0.25 * ps
    return round(max(0.25, min(1.0, raw)), 4)


def calc_units(r, mode: str) -> float:
    price = float(r.get("priceSP") or 0)
    score = float(r.get("pfaiScore") or 70)
    if price <= 1:
        return 0.0
    implied   = (1.0 / price) * 100.0
    pf_boost  = max(0.0, (score - 70) / 2.0)
    win_prob  = min(85.0, implied + pf_boost) / 100.0
    edge      = (win_prob * price - 1) / (price - 1)
    if edge <= 0:
        return 0.0
    return 1.0


def market_rank(runner_name: str, runners: list) -> int:
    sorted_runners = sorted(runners, key=lambda x: float(x.get("priceSP") or 99))
    for i, r in enumerate(sorted_runners, 1):
        if r.get("name", "").lower() == runner_name.lower():
            return i
    return 999


# ── Main ───────────────────────────────────────────────────────────────────
def generate():
    day_files = sorted(f for f in os.listdir(PF_CACHE) if f.startswith("day_"))
    print(f"Processing {len(day_files)} days...")

    seed_bets = []
    seen_ids  = set()
    now_str   = datetime.now(timezone.utc).isoformat()

    snipe_bets = snipe_wins = 0
    bet_bets   = bet_wins   = 0

    for df in day_files:
        with open(os.path.join(PF_CACHE, df)) as f:
            day_data = json.load(f)

        date_str = day_data["date"]  # "2026-01-18"
        dt_base  = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=AEDT)

        for meeting in day_data.get("meetings", []):
            track   = meeting.get("track", "Unknown")
            races   = meeting.get("races", {})

            for race_no_str, race in races.items():
                race_no  = int(race_no_str)
                runners  = race.get("runners", [])

                # Build active runners (position > 0 means they ran)
                active = [r for r in runners if r.get("position") and int(r.get("position", 0)) > 0]
                if not active:
                    continue

                # Use a fake start time (noon AEDT) — exact time not in PF cache
                race_time = dt_base.replace(hour=12, minute=0, second=0) + timedelta(minutes=race_no * 30)

                # Gather qualifying runners for each system
                snipe_cands = [(r, r.get("pfaiScore", 0), market_rank(r["name"], active))
                               for r in active if is_snipe(r)]
                bet_cands   = [(r, r.get("pfaiScore", 0), market_rank(r["name"], active))
                               for r in active if is_nex_bet(r)]

                def pick_best(cands):
                    if not cands:
                        return None
                    return sorted(cands, key=lambda x: (-x[1], x[2]))[0][0]

                for runner, mode, bet_type in [
                    (pick_best(snipe_cands), "SNIPER",   "NEX SNIPE"),
                    (pick_best(bet_cands),   "HIGH_VOL", "NEX BET"),
                ]:
                    if runner is None:
                        continue

                    price    = float(runner.get("priceSP") or 0)
                    if price <= 0:
                        continue

                    units    = calc_units(runner, mode)
                    if units <= 0:
                        continue

                    position = int(runner.get("position") or 99)
                    result   = "win" if position == 1 else "loss"
                    score    = float(runner.get("pfaiScore") or 70)
                    mkt_rank = market_rank(runner["name"], active)
                    tab_no   = int(runner.get("tabNo") or 0)

                    bet_id = f"{track}_R{race_no}_{runner['name']}_{date_str.replace('-','')}_{bet_type.replace(' ','')}"
                    if bet_id in seen_ids:
                        continue
                    seen_ids.add(bet_id)

                    bet = {
                        "id":                 bet_id,
                        "track":              track,
                        "race_num":           race_no,
                        "horse_name":         runner["name"],
                        "horse_num":          tab_no,
                        "price":              price,
                        "units":              units,
                        "rsi":                round(score),
                        "market_rank":        mkt_rank,
                        "bet_type":           bet_type,
                        "race_time":          race_time.isoformat(),
                        "recorded_at":        now_str,
                        "result":             result,
                        "finishing_position": position,
                        "settled_at":         now_str,
                    }
                    seed_bets.append(bet)

                    if bet_type == "NEX SNIPE":
                        snipe_bets += 1
                        if result == "win": snipe_wins += 1
                    else:
                        bet_bets += 1
                        if result == "win": bet_wins += 1

    # Save
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_seed.json")
    with open(out_path, "w") as f:
        json.dump(seed_bets, f, indent=2)

    print(f"\n✓ Saved {len(seed_bets)} bets → {out_path}")
    print(f"\n  NEX SNIPE : {snipe_bets} bets  {snipe_wins} wins  "
          f"({snipe_wins/snipe_bets*100:.1f}% SR)" if snipe_bets else "  NEX SNIPE : 0 bets")
    print(f"  NEX BET   : {bet_bets} bets  {bet_wins} wins  "
          f"({bet_wins/bet_bets*100:.1f}% SR)" if bet_bets else "  NEX BET   : 0 bets")

    # Quick ROI calc
    for label, bets_list, wins_count in [
        ("NEX SNIPE", [b for b in seed_bets if b["bet_type"]=="NEX SNIPE"], snipe_wins),
        ("NEX BET",   [b for b in seed_bets if b["bet_type"]=="NEX BET"],   bet_wins),
    ]:
        if not bets_list: continue
        staked = sum(b["units"] for b in bets_list)
        returned = sum(b["units"] * b["price"] for b in bets_list if b["result"]=="win")
        profit = returned - staked
        roi = profit / staked * 100 if staked else 0
        print(f"  {label}: staked={staked:.1f}u  profit={profit:+.1f}u  ROI={roi:+.1f}%")


if __name__ == "__main__":
    generate()
