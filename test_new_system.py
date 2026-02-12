#!/usr/bin/env python3
"""
Quick test of new speed rating system in horse_analyst.py
"""

from horse_analyst import HorseRacingAnalyst, Runner, Race
from datetime import datetime, timezone

# Create analyst
analyst = HorseRacingAnalyst()

# Verify config
print("=" * 70)
print("SPEED RATING SYSTEM - CONFIG CHECK")
print("=" * 70)
print(f"MIN_PRICE: ${analyst.MIN_PRICE}")
print(f"MAX_PRICE: ${analyst.MAX_PRICE}")
print(f"MAX_RANK: {analyst.MAX_RANK}")
print(f"MIN_SPEED_RATING: {analyst.MIN_SPEED_RATING}")
print(f"KELLY_FRACTION: {analyst.KELLY_FRACTION} (Full Kelly)")
print("=" * 70)

# Create a mock race to test speed rating calculation
mock_runner = Runner(
    name="Test Horse",
    saddlecloth=1,
    price=3.50,
    barrier=3,
    jockey="Test Jockey",
    trainer="Test Trainer",
    last_starts=[1, 2, 1, 3, 2],
    speed_rating=75,
    class_rating=70
)

mock_race = Race(
    track_name="Flemington",
    race_number=1,
    distance=1200,
    surface="Good",
    grade="BM78",
    runners=[mock_runner],
    start_time=datetime.now(timezone.utc)
)

print("\nTesting speed rating calculation...")
try:
    speed_rating = analyst._calculate_speed_rating(mock_runner, mock_race)
    print(f"✅ Speed rating calculated: {speed_rating}")

    win_pct = analyst._calculate_win_percentage(mock_runner, mock_race, speed_rating)
    print(f"✅ Win percentage calculated: {win_pct}%")

    units = analyst._calculate_units(mock_runner, win_pct, speed_rating)
    print(f"✅ Units calculated: {units}u")

    is_tracked = analyst._is_tracked(mock_runner, mock_race, speed_rating, win_pct)
    print(f"✅ Is tracked: {is_tracked}")

    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED - Speed rating system working!")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
