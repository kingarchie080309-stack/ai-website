#!/usr/bin/env python3
"""
Test different price ranges to compare ROI
"""

import json
import os
from calculate_speed_ratings import SpeedRatingCalculator

CACHE_DIR = os.path.expanduser('~/racing_data_cache')

# Test configs
TEST_CONFIGS = [
    {"name": "$2-$5 (CURRENT)", "min": 2.0, "max": 5.0},
    {"name": "$2-$7", "min": 2.0, "max": 7.0},
    {"name": "$2-$10", "min": 2.0, "max": 10.0},
    {"name": "$2-$15", "min": 2.0, "max": 15.0},
]

MAX_RANK = 2
MIN_SPEED_RATING = 70
KELLY_FRACTION = 1.0


def calculate_kelly_units(win_probability: float, price: float, max_units: float = 4.0) -> float:
    if win_probability <= 0 or price <= 1:
        return 0.0
    edge = (win_probability * price - 1) / (price - 1)
    if edge <= 0:
        return 0.0
    kelly_bet = KELLY_FRACTION * edge
    return min(kelly_bet, max_units)


def estimate_win_probability(speed_rating: int, market_rank: int) -> float:
    base_prob = (speed_rating - 50) / 50 * 0.6 + 0.3
    base_prob = max(0.1, min(0.9, base_prob))
    if market_rank == 1:
        multiplier = 1.0
    elif market_rank == 2:
        multiplier = 0.8
    else:
        multiplier = 0.6
    return base_prob * multiplier


def backtest_config(min_price, max_price):
    """Run backtest with specific price range"""
    calculator = SpeedRatingCalculator()
    meets_files = sorted([f for f in os.listdir(CACHE_DIR) if f.startswith('meets_')])

    all_bets = []

    for meets_file in meets_files:
        with open(os.path.join(CACHE_DIR, meets_file)) as f:
            meets_data = json.load(f)

        for meet in meets_data.get('meets', []):
            meet_id = meet.get('meet_id', '')
            races_file = os.path.join(CACHE_DIR, f'races_{meet_id}.json')

            if not os.path.exists(races_file):
                continue

            with open(races_file) as f:
                races_data = json.load(f)

            for race_detail in races_data.get('races', []):
                # Skip trials
                race_name = (race_detail.get('race_name') or '').upper()
                race_class = (race_detail.get('class') or '').upper()

                if ('TRIAL' in race_name or 'TRIAL' in race_class or
                    'JUMP OUT' in race_name or 'JUMP OUT' in race_class or
                    '-TRL' in race_class or race_class.endswith('TRL')):
                    continue

                # Check bookmaker odds
                runners_with_odds = sum(1 for r in race_detail.get('runners', [])
                                       if r.get('odds') and len(r.get('odds', [])) > 0)
                total_runners = len([r for r in race_detail.get('runners', [])
                                    if not r.get('scratched', False)])

                if total_runners > 0 and runners_with_odds < (total_runners * 0.5):
                    continue

                # Only races with results
                has_results = any(r.get('position') for r in race_detail.get('runners', []))
                if not has_results:
                    continue

                # Calculate ratings for all runners
                runners_with_ratings = []

                for runner_data in race_detail.get('runners', []):
                    if runner_data.get('scratched', False):
                        continue

                    # Get price
                    price = 5.0
                    odds_array = runner_data.get('odds', [])
                    if odds_array:
                        for odds_entry in odds_array:
                            if odds_entry.get('bookmaker') == 'Sportsbet':
                                price = float(odds_entry.get('win_odds', 5.0))
                                break
                        else:
                            price = float(odds_array[0].get('win_odds', 5.0))

                    # Calculate speed rating
                    rating = calculator.calculate_speed_rating(runner_data, race_detail)

                    # Get position
                    position = runner_data.get('position')
                    try:
                        pos_int = int(position) if position else 999
                    except (ValueError, TypeError):
                        pos_int = 999

                    runners_with_ratings.append({
                        'horse': runner_data.get('horse', 'Unknown'),
                        'rating': rating,
                        'position': pos_int,
                        'price': price
                    })

                if len(runners_with_ratings) < 2:
                    continue

                # Sort by rating (highest first)
                runners_with_ratings.sort(key=lambda x: x['rating'], reverse=True)

                # Get top-rated horse
                top_runner = runners_with_ratings[0]

                # Apply filters - USE THE CONFIG PRICE RANGE
                if top_runner['price'] < min_price or top_runner['price'] > max_price:
                    continue

                if top_runner['rating'] < MIN_SPEED_RATING:
                    continue

                # Get market rank (by price)
                sorted_by_price = sorted(runners_with_ratings, key=lambda x: x['price'])
                market_rank = next((i+1 for i, r in enumerate(sorted_by_price)
                                   if r['horse'] == top_runner['horse']), 999)

                if market_rank > MAX_RANK:
                    continue

                # Calculate Kelly units
                win_prob = estimate_win_probability(top_runner['rating'], market_rank)
                units = calculate_kelly_units(win_prob, top_runner['price'])

                if units <= 0:
                    continue

                # Record bet
                won = top_runner['position'] == 1
                pnl = units * (top_runner['price'] - 1.0) if won else -units

                all_bets.append({
                    'price': top_runner['price'],
                    'rating': top_runner['rating'],
                    'market_rank': market_rank,
                    'units': units,
                    'won': won,
                    'pnl': pnl
                })

    return all_bets


# Run tests
print("=" * 80)
print("PRICE RANGE COMPARISON - Speed Rating System")
print("=" * 80)
print(f"\nFixed filters: Rank 1-{MAX_RANK}, Rating {MIN_SPEED_RATING}+, Full Kelly\n")

results = []

for config in TEST_CONFIGS:
    print(f"Testing {config['name']}...")
    bets = backtest_config(config['min'], config['max'])

    if not bets:
        print(f"  ❌ No bets\n")
        continue

    wins = sum(1 for b in bets if b['won'])
    total_staked = sum(b['units'] for b in bets)
    total_pnl = sum(b['pnl'] for b in bets)
    roi = (total_pnl / total_staked * 100) if total_staked > 0 else 0
    avg_price = sum(b['price'] for b in bets) / len(bets)

    results.append({
        'config': config['name'],
        'min_price': config['min'],
        'max_price': config['max'],
        'bets': len(bets),
        'wins': wins,
        'win_rate': wins / len(bets) * 100,
        'staked': total_staked,
        'pnl': total_pnl,
        'roi': roi,
        'avg_price': avg_price,
        'bets_per_day': len(bets) / 200
    })

    print(f"  ✅ {len(bets)} bets, {wins} wins ({wins/len(bets)*100:.1f}%), {roi:+.1f}% ROI\n")

# Summary table
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\n{'Config':<20} {'Bets':<8} {'Win%':<8} {'ROI':<10} {'Avg$':<8} {'Bets/Day':<10}")
print("-" * 80)

for r in results:
    print(f"{r['config']:<20} {r['bets']:<8} {r['win_rate']:>6.1f}% {r['roi']:>+8.1f}% ${r['avg_price']:>6.2f} {r['bets_per_day']:>9.1f}")

print("\n" + "=" * 80)
print("DETAILED BREAKDOWN")
print("=" * 80)

for r in results:
    print(f"\n{r['config']}:")
    print(f"  Total bets: {r['bets']}")
    print(f"  Wins: {r['wins']} ({r['win_rate']:.1f}%)")
    print(f"  Total staked: {r['staked']:.2f}u")
    print(f"  Profit/Loss: {r['pnl']:+.2f}u")
    print(f"  ROI: {r['roi']:+.1f}%")
    print(f"  Avg price: ${r['avg_price']:.2f}")
    print(f"  Bets per day: {r['bets_per_day']:.1f}")

print("\n" + "=" * 80)
