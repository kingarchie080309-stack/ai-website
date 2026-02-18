"""
HORSE RACING AI - SPEED RATING SYSTEM
Production horse racing analysis with speed ratings and Full Kelly staking
Filters: $2-$10, Rank 1-2, 70+ speed rating
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Callable, Any
from datetime import datetime, timezone, timedelta
AEDT = timezone(timedelta(hours=11))  # Australian Eastern Daylight Time (UTC+11)
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

# Backtest seed — 233 bets (NEX SNIPE + NEX BET, Jan 18–Feb 18 2026)
_BACKTEST_SEED = json.loads('[{"id":"Armidale_R4_Arrabbiata_20260118_NEXSNIPE","track":"Armidale","race_num":4,"horse_name":"Arrabbiata","horse_num":2,"price":6.0,"units":0.08,"rsi":91,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-01-18T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":6,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Armidale_R4_Arrabbiata_20260118_NEXBET","track":"Armidale","race_num":4,"horse_name":"Arrabbiata","horse_num":2,"price":6.0,"units":0.1,"rsi":91,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-18T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":6,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Cowra_R3_Vicious Rumour_20260118_NEXBET","track":"Cowra","race_num":3,"horse_name":"Vicious Rumour","horse_num":10,"price":5.0,"units":0.04,"rsi":80,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-01-18T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Cowra_R7_Zale_20260118_NEXSNIPE","track":"Cowra","race_num":7,"horse_name":"Zale","horse_num":10,"price":3.0,"units":0.08,"rsi":86,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-01-18T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Cowra_R7_Zale_20260118_NEXBET","track":"Cowra","race_num":7,"horse_name":"Zale","horse_num":10,"price":3.0,"units":0.09,"rsi":86,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-18T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Hobart_R5_Gingerson_20260118_NEXBET","track":"Hobart","race_num":5,"horse_name":"Gingerson","horse_num":4,"price":7.0,"units":0.08,"rsi":89,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-01-18T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Hobart_R6_Geegees Missile_20260118_NEXSNIPE","track":"Hobart","race_num":6,"horse_name":"Geegees Missile","horse_num":1,"price":3.2,"units":0.08,"rsi":89,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-01-18T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Hobart_R6_Geegees Missile_20260118_NEXBET","track":"Hobart","race_num":6,"horse_name":"Geegees Missile","horse_num":1,"price":3.2,"units":0.09,"rsi":89,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-18T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Mt Barker_R3_Ah Kum_20260118_NEXBET","track":"Mt Barker","race_num":3,"horse_name":"Ah Kum","horse_num":3,"price":3.5,"units":0.05,"rsi":82,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-18T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":6,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Mt Barker_R8_Timeless Gem_20260118_NEXBET","track":"Mt Barker","race_num":8,"horse_name":"Timeless Gem","horse_num":7,"price":5.0,"units":0.05,"rsi":83,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-18T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":7,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Mt Barker_R9_Ma Ma Belle_20260118_NEXBET","track":"Mt Barker","race_num":9,"horse_name":"Ma Ma Belle","horse_num":6,"price":3.2,"units":0.05,"rsi":80,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-18T16:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Gunnedah_R6_Haiku Star_20260119_NEXBET","track":"Gunnedah","race_num":6,"horse_name":"Haiku Star","horse_num":1,"price":5.5,"units":0.02,"rsi":75,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-19T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Geelong_R7_Ultra Blue_20260120_NEXSNIPE","track":"Geelong","race_num":7,"horse_name":"Ultra Blue","horse_num":2,"price":3.3,"units":0.12,"rsi":91,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-01-20T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Geelong_R7_Ultra Blue_20260120_NEXBET","track":"Geelong","race_num":7,"horse_name":"Ultra Blue","horse_num":2,"price":3.3,"units":0.13,"rsi":91,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-20T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ipswich_R6_Lumens Lenny_20260121_NEXBET","track":"Ipswich","race_num":6,"horse_name":"Lumens Lenny","horse_num":6,"price":4.8,"units":0.02,"rsi":76,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-21T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ipswich_R4_Ratenotice_20260121_NEXBET","track":"Ipswich","race_num":4,"horse_name":"Ratenotice","horse_num":15,"price":4.2,"units":0.02,"rsi":76,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-21T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ipswich_R7_Jimmyinthejungle_20260121_NEXBET","track":"Ipswich","race_num":7,"horse_name":"Jimmyinthejungle","horse_num":5,"price":6.5,"units":0.02,"rsi":78,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-21T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":10,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Bunbury_R7_Bird On A Wire_20260121_NEXBET","track":"Bunbury","race_num":7,"horse_name":"Bird On A Wire","horse_num":5,"price":5.5,"units":0.12,"rsi":94,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-21T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":8,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Randwick-Kensington_R5_Vanessi_20260121_NEXBET","track":"Randwick-Kensington","race_num":5,"horse_name":"Vanessi","horse_num":7,"price":5.0,"units":0.01,"rsi":73,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-21T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Randwick-Kensington_R7_Existential Bob_20260121_NEXBET","track":"Randwick-Kensington","race_num":7,"horse_name":"Existential Bob","horse_num":5,"price":5.5,"units":0.03,"rsi":78,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-21T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":5,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Sandown-Hillside_R5_Brandjam_20260121_NEXBET","track":"Sandown-Hillside","race_num":5,"horse_name":"Brandjam","horse_num":7,"price":3.4,"units":0.01,"rsi":73,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-21T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Sandown-Hillside_R8_Savamoon_20260121_NEXBET","track":"Sandown-Hillside","race_num":8,"horse_name":"Savamoon","horse_num":3,"price":2.7,"units":0.1,"rsi":85,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-21T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Tamworth_R2_Sipping Shamus_20260122_NEXBET","track":"Tamworth","race_num":2,"horse_name":"Sipping Shamus","horse_num":4,"price":3.3,"units":0.17,"rsi":95,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-22T13:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Tamworth_R6_Call Me Terry_20260122_NEXBET","track":"Tamworth","race_num":6,"horse_name":"Call Me Terry","horse_num":8,"price":8.0,"units":0.06,"rsi":85,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-01-22T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":7,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Tamworth_R7_Zoomorphic_20260122_NEXBET","track":"Tamworth","race_num":7,"horse_name":"Zoomorphic","horse_num":3,"price":6.5,"units":0.02,"rsi":76,"market_rank":5,"bet_type":"NEX BET","race_time":"2026-01-22T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":9,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Kembla Grange_R1_Kitty Okay_20260122_NEXSNIPE","track":"Kembla Grange","race_num":1,"horse_name":"Kitty Okay","horse_num":6,"price":2.7,"units":0.09,"rsi":86,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-01-22T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Kembla Grange_R1_Kitty Okay_20260122_NEXBET","track":"Kembla Grange","race_num":1,"horse_name":"Kitty Okay","horse_num":6,"price":2.7,"units":0.1,"rsi":86,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-22T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Warwick_R1_Miss Highfalutin_20260122_NEXSNIPE","track":"Warwick","race_num":1,"horse_name":"Miss Highfalutin","horse_num":14,"price":4.2,"units":0.16,"rsi":100,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-01-22T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Warwick_R1_Miss Highfalutin_20260122_NEXBET","track":"Warwick","race_num":1,"horse_name":"Miss Highfalutin","horse_num":14,"price":4.2,"units":0.16,"rsi":100,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-22T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Warwick_R3_Airswing_20260122_NEXBET","track":"Warwick","race_num":3,"horse_name":"Airswing","horse_num":2,"price":4.6,"units":0.01,"rsi":73,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-22T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Warwick_R5_Petite Palace_20260122_NEXBET","track":"Warwick","race_num":5,"horse_name":"Petite Palace","horse_num":10,"price":3.3,"units":0.05,"rsi":82,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-22T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Cranbourne_R7_Night Flash_20260122_NEXSNIPE","track":"Cranbourne","race_num":7,"horse_name":"Night Flash","horse_num":4,"price":4.2,"units":0.02,"rsi":82,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-01-22T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Cranbourne_R7_Night Flash_20260122_NEXBET","track":"Cranbourne","race_num":7,"horse_name":"Night Flash","horse_num":4,"price":4.2,"units":0.04,"rsi":82,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-22T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Moruya_R7_Dolzino_20260123_NEXBET","track":"Moruya","race_num":7,"horse_name":"Dolzino","horse_num":1,"price":5.5,"units":0.01,"rsi":74,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-23T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":6,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Port Macquarie_R7_Moscow Circus_20260123_NEXBET","track":"Port Macquarie","race_num":7,"horse_name":"Moscow Circus","horse_num":6,"price":2.6,"units":0.01,"rsi":73,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-23T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Canterbury_R7_Kimberley Secrets_20260123_NEXSNIPE","track":"Canterbury","race_num":7,"horse_name":"Kimberley Secrets","horse_num":3,"price":4.2,"units":0.05,"rsi":83,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-01-23T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Canterbury_R7_Kimberley Secrets_20260123_NEXBET","track":"Canterbury","race_num":7,"horse_name":"Kimberley Secrets","horse_num":3,"price":4.2,"units":0.06,"rsi":83,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-23T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Canterbury_R5_Steel Strike_20260123_NEXBET","track":"Canterbury","race_num":5,"horse_name":"Steel Strike","horse_num":5,"price":2.8,"units":0.13,"rsi":91,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-23T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":6,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Emerald_R3_Sideshow Frankie_20260123_NEXSNIPE","track":"Emerald","race_num":3,"horse_name":"Sideshow Frankie","horse_num":2,"price":3.6,"units":0.04,"rsi":80,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-01-23T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Emerald_R3_Sideshow Frankie_20260123_NEXBET","track":"Emerald","race_num":3,"horse_name":"Sideshow Frankie","horse_num":2,"price":3.6,"units":0.05,"rsi":80,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-23T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Gold Coast_R3_Razors_20260123_NEXSNIPE","track":"Gold Coast","race_num":3,"horse_name":"Razors","horse_num":3,"price":7.5,"units":0.09,"rsi":92,"market_rank":5,"bet_type":"NEX SNIPE","race_time":"2026-01-23T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":7,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Gold Coast_R3_Razors_20260123_NEXBET","track":"Gold Coast","race_num":3,"horse_name":"Razors","horse_num":3,"price":7.5,"units":0.09,"rsi":92,"market_rank":5,"bet_type":"NEX BET","race_time":"2026-01-23T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":7,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Gold Coast_R7_Kadall_20260123_NEXBET","track":"Gold Coast","race_num":7,"horse_name":"Kadall","horse_num":3,"price":4.0,"units":0.1,"rsi":89,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-23T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":10,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Port Lincoln_R1_Grecian Storm_20260123_NEXBET","track":"Port Lincoln","race_num":1,"horse_name":"Grecian Storm","horse_num":11,"price":4.4,"units":0.03,"rsi":79,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-23T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Port Lincoln_R2_Game Over_20260123_NEXBET","track":"Port Lincoln","race_num":2,"horse_name":"Game Over","horse_num":1,"price":3.4,"units":0.06,"rsi":84,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-23T13:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Launceston_R3_Vortistar_20260123_NEXBET","track":"Launceston","race_num":3,"horse_name":"Vortistar","horse_num":9,"price":4.8,"units":0.05,"rsi":84,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-23T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Geraldton_R4_Queen Of Hawks_20260123_NEXBET","track":"Geraldton","race_num":4,"horse_name":"Queen Of Hawks","horse_num":2,"price":2.7,"units":0.04,"rsi":78,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-23T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":6,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Pakenham_R4_Shinjina_20260123_NEXBET","track":"Pakenham","race_num":4,"horse_name":"Shinjina","horse_num":5,"price":2.7,"units":0.01,"rsi":77,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-23T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Pakenham_R8_Stage \'n\' Screen_20260123_NEXBET","track":"Pakenham","race_num":8,"horse_name":"Stage \'n\' Screen","horse_num":2,"price":4.2,"units":0.02,"rsi":78,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-23T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Newcastle_R7_Monte Veebee_20260124_NEXBET","track":"Newcastle","race_num":7,"horse_name":"Monte Veebee","horse_num":11,"price":2.7,"units":0.03,"rsi":78,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-24T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Murwillumbah_R3_Fanci Fleur_20260124_NEXBET","track":"Murwillumbah","race_num":3,"horse_name":"Fanci Fleur","horse_num":8,"price":7.5,"units":0.02,"rsi":76,"market_rank":5,"bet_type":"NEX BET","race_time":"2026-01-24T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":9,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Randwick_R2_Promitto_20260124_NEXSNIPE","track":"Randwick","race_num":2,"horse_name":"Promitto","horse_num":2,"price":8.0,"units":0.04,"rsi":84,"market_rank":6,"bet_type":"NEX SNIPE","race_time":"2026-01-24T13:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Randwick_R2_Promitto_20260124_NEXBET","track":"Randwick","race_num":2,"horse_name":"Promitto","horse_num":2,"price":8.0,"units":0.05,"rsi":84,"market_rank":6,"bet_type":"NEX BET","race_time":"2026-01-24T13:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Townsville_R4_Buffet Buster_20260124_NEXBET","track":"Townsville","race_num":4,"horse_name":"Buffet Buster","horse_num":5,"price":2.8,"units":0.05,"rsi":80,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-24T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Townsville_R7_Henry\'s Blade_20260124_NEXBET","track":"Townsville","race_num":7,"horse_name":"Henry\'s Blade","horse_num":8,"price":5.0,"units":0.05,"rsi":84,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-01-24T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ascot_R8_Cut The Talk_20260124_NEXSNIPE","track":"Ascot","race_num":8,"horse_name":"Cut The Talk","horse_num":7,"price":4.2,"units":0.03,"rsi":84,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-01-24T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ascot_R8_Cut The Talk_20260124_NEXBET","track":"Ascot","race_num":8,"horse_name":"Cut The Talk","horse_num":7,"price":4.2,"units":0.05,"rsi":84,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-24T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Pioneer Park_R3_Buckleup Buddy_20260124_NEXBET","track":"Pioneer Park","race_num":3,"horse_name":"Buckleup Buddy","horse_num":2,"price":7.5,"units":0.02,"rsi":77,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-24T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Pioneer Park_R5_Mummsie_20260124_NEXSNIPE","track":"Pioneer Park","race_num":5,"horse_name":"Mummsie","horse_num":5,"price":3.5,"units":0.13,"rsi":92,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-01-24T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Pioneer Park_R5_Mummsie_20260124_NEXBET","track":"Pioneer Park","race_num":5,"horse_name":"Mummsie","horse_num":5,"price":3.5,"units":0.14,"rsi":92,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-24T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Grafton_R1_Alaska Dream_20260125_NEXSNIPE","track":"Grafton","race_num":1,"horse_name":"Alaska Dream","horse_num":1,"price":2.8,"units":0.09,"rsi":89,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-01-25T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Grafton_R1_Alaska Dream_20260125_NEXBET","track":"Grafton","race_num":1,"horse_name":"Alaska Dream","horse_num":1,"price":2.8,"units":0.12,"rsi":89,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-25T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Moe_R8_Itsukushima_20260125_NEXBET","track":"Moe","race_num":8,"horse_name":"Itsukushima","horse_num":2,"price":3.1,"units":0.07,"rsi":84,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-25T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Mt Gambier_R5_Cork Harbour_20260125_NEXBET","track":"Mt Gambier","race_num":5,"horse_name":"Cork Harbour","horse_num":5,"price":7.5,"units":0.11,"rsi":95,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-01-25T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":6,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Mt Gambier_R7_Dartboard_20260125_NEXBET","track":"Mt Gambier","race_num":7,"horse_name":"Dartboard","horse_num":7,"price":3.8,"units":0.12,"rsi":93,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-25T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Hobart_R4_Gingerson_20260125_NEXSNIPE","track":"Hobart","race_num":4,"horse_name":"Gingerson","horse_num":4,"price":4.4,"units":0.14,"rsi":96,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-01-25T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":7,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Hobart_R4_Gingerson_20260125_NEXBET","track":"Hobart","race_num":4,"horse_name":"Gingerson","horse_num":4,"price":4.4,"units":0.15,"rsi":96,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-25T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":7,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Kilcoy_R5_Purosangue_20260126_NEXBET","track":"Kilcoy","race_num":5,"horse_name":"Purosangue","horse_num":1,"price":4.4,"units":0.03,"rsi":78,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-26T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Geelong_R5_Thailess_20260126_NEXBET","track":"Geelong","race_num":5,"horse_name":"Thailess","horse_num":5,"price":8.0,"units":0.02,"rsi":77,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-01-26T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Geelong_R6_Revolver_20260126_NEXSNIPE","track":"Geelong","race_num":6,"horse_name":"Revolver","horse_num":5,"price":6.5,"units":0.05,"rsi":85,"market_rank":4,"bet_type":"NEX SNIPE","race_time":"2026-01-26T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Geelong_R6_Revolver_20260126_NEXBET","track":"Geelong","race_num":6,"horse_name":"Revolver","horse_num":5,"price":6.5,"units":0.06,"rsi":85,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-01-26T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Hanging Rock_R4_Dionisio_20260126_NEXSNIPE","track":"Hanging Rock","race_num":4,"horse_name":"Dionisio","horse_num":2,"price":3.3,"units":0.08,"rsi":86,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-01-26T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Hanging Rock_R4_Dionisio_20260126_NEXBET","track":"Hanging Rock","race_num":4,"horse_name":"Dionisio","horse_num":2,"price":3.3,"units":0.09,"rsi":86,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-26T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Hanging Rock_R7_Whistler Girl_20260126_NEXBET","track":"Hanging Rock","race_num":7,"horse_name":"Whistler Girl","horse_num":9,"price":3.4,"units":0.04,"rsi":80,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-26T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Bunbury_R6_Coondle_20260126_NEXBET","track":"Bunbury","race_num":6,"horse_name":"Coondle","horse_num":7,"price":7.0,"units":0.08,"rsi":91,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-26T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":5,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Wagga_R7_Fourthtimelucky_20260126_NEXBET","track":"Wagga","race_num":7,"horse_name":"Fourthtimelucky","horse_num":3,"price":4.4,"units":0.1,"rsi":91,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-26T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ascot_R4_Naughty Tortie_20260128_NEXBET","track":"Ascot","race_num":4,"horse_name":"Naughty Tortie","horse_num":1,"price":8.0,"units":0.05,"rsi":84,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-28T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ascot_R3_Don\'t Wink_20260128_NEXBET","track":"Ascot","race_num":3,"horse_name":"Don\'t Wink","horse_num":7,"price":2.9,"units":0.17,"rsi":98,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-28T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Scone_R7_Vierville_20260129_NEXBET","track":"Scone","race_num":7,"horse_name":"Vierville","horse_num":2,"price":4.0,"units":0.01,"rsi":72,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-29T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Albany_R3_Village Girl_20260129_NEXBET","track":"Albany","race_num":3,"horse_name":"Village Girl","horse_num":6,"price":3.8,"units":0.04,"rsi":84,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-29T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Albany_R8_Lordgivemestrength_20260129_NEXBET","track":"Albany","race_num":8,"horse_name":"Lordgivemestrength","horse_num":11,"price":5.5,"units":0.02,"rsi":79,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-29T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":6,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Pakenham_R7_Betwitchery_20260129_NEXSNIPE","track":"Pakenham","race_num":7,"horse_name":"Betwitchery","horse_num":2,"price":3.1,"units":0.05,"rsi":84,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-01-29T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Pakenham_R7_Betwitchery_20260129_NEXBET","track":"Pakenham","race_num":7,"horse_name":"Betwitchery","horse_num":2,"price":3.1,"units":0.06,"rsi":84,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-29T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Taree_R2_Jade Trees_20260130_NEXBET","track":"Taree","race_num":2,"horse_name":"Jade Trees","horse_num":1,"price":3.1,"units":0.02,"rsi":77,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-30T13:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Taree_R6_Get Some Fun_20260130_NEXSNIPE","track":"Taree","race_num":6,"horse_name":"Get Some Fun","horse_num":2,"price":4.0,"units":0.06,"rsi":84,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-01-30T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Taree_R6_Get Some Fun_20260130_NEXBET","track":"Taree","race_num":6,"horse_name":"Get Some Fun","horse_num":2,"price":4.0,"units":0.07,"rsi":84,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-30T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Canterbury_R3_Albany Road_20260130_NEXBET","track":"Canterbury","race_num":3,"horse_name":"Albany Road","horse_num":6,"price":2.8,"units":0.05,"rsi":82,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-30T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Canterbury_R4_Calga Power_20260130_NEXBET","track":"Canterbury","race_num":4,"horse_name":"Calga Power","horse_num":6,"price":3.1,"units":0.18,"rsi":98,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-30T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Dalby_R8_Cardiologist_20260130_NEXBET","track":"Dalby","race_num":8,"horse_name":"Cardiologist","horse_num":1,"price":5.0,"units":0.01,"rsi":74,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-30T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Launceston_R4_Street Diva_20260130_NEXBET","track":"Launceston","race_num":4,"horse_name":"Street Diva","horse_num":1,"price":2.6,"units":0.11,"rsi":87,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-30T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Launceston_R7_Material Madam_20260130_NEXSNIPE","track":"Launceston","race_num":7,"horse_name":"Material Madam","horse_num":6,"price":4.4,"units":0.02,"rsi":80,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-01-30T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Launceston_R7_Material Madam_20260130_NEXBET","track":"Launceston","race_num":7,"horse_name":"Material Madam","horse_num":6,"price":4.4,"units":0.04,"rsi":80,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-30T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Newcastle_R6_Fiorsum Fred_20260131_NEXSNIPE","track":"Newcastle","race_num":6,"horse_name":"Fiorsum Fred","horse_num":4,"price":6.5,"units":0.04,"rsi":83,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-01-31T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Newcastle_R6_Fiorsum Fred_20260131_NEXBET","track":"Newcastle","race_num":6,"horse_name":"Fiorsum Fred","horse_num":4,"price":6.5,"units":0.05,"rsi":83,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-31T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Newcastle_R7_Throttle Response_20260131_NEXBET","track":"Newcastle","race_num":7,"horse_name":"Throttle Response","horse_num":8,"price":5.5,"units":0.03,"rsi":78,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-31T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Rosehill_R9_Cormac T_20260131_NEXSNIPE","track":"Rosehill","race_num":9,"horse_name":"Cormac T","horse_num":2,"price":6.5,"units":0.03,"rsi":80,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-01-31T16:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Rosehill_R9_Cormac T_20260131_NEXBET","track":"Rosehill","race_num":9,"horse_name":"Cormac T","horse_num":2,"price":6.5,"units":0.03,"rsi":80,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-31T16:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Bundaberg_R2_Aces Up_20260131_NEXSNIPE","track":"Bundaberg","race_num":2,"horse_name":"Aces Up","horse_num":1,"price":3.4,"units":0.12,"rsi":94,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-01-31T13:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Bundaberg_R2_Aces Up_20260131_NEXBET","track":"Bundaberg","race_num":2,"horse_name":"Aces Up","horse_num":1,"price":3.4,"units":0.14,"rsi":94,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-31T13:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ipswich_R6_Run Lucy Run_20260131_NEXBET","track":"Ipswich","race_num":6,"horse_name":"Run Lucy Run","horse_num":8,"price":2.5,"units":0.01,"rsi":73,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-31T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Eagle Farm_R9_Wondereach_20260131_NEXBET","track":"Eagle Farm","race_num":9,"horse_name":"Wondereach","horse_num":9,"price":7.5,"units":0.12,"rsi":96,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-01-31T16:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":9,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Kyneton_R8_Brutal World_20260131_NEXBET","track":"Kyneton","race_num":8,"horse_name":"Brutal World","horse_num":7,"price":4.4,"units":0.01,"rsi":75,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-31T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":9,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Morphettville_R8_Sghirripa_20260131_NEXSNIPE","track":"Morphettville","race_num":8,"horse_name":"Sghirripa","horse_num":2,"price":6.0,"units":0.07,"rsi":86,"market_rank":4,"bet_type":"NEX SNIPE","race_time":"2026-01-31T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Morphettville_R8_Sghirripa_20260131_NEXBET","track":"Morphettville","race_num":8,"horse_name":"Sghirripa","horse_num":2,"price":6.0,"units":0.08,"rsi":86,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-01-31T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Esperance_R5_Razmas_20260131_NEXBET","track":"Esperance","race_num":5,"horse_name":"Razmas","horse_num":4,"price":7.5,"units":0.03,"rsi":79,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-31T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ascot_R1_Tycoon Harry_20260131_NEXBET","track":"Ascot","race_num":1,"horse_name":"Tycoon Harry","horse_num":6,"price":3.1,"units":0.02,"rsi":77,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-31T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":6,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ascot_R2_Twisted Steel_20260131_NEXBET","track":"Ascot","race_num":2,"horse_name":"Twisted Steel","horse_num":1,"price":3.5,"units":0.12,"rsi":90,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-01-31T13:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ascot_R4_Sonoftheboss_20260131_NEXSNIPE","track":"Ascot","race_num":4,"horse_name":"Sonoftheboss","horse_num":1,"price":5.0,"units":0.06,"rsi":86,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-01-31T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ascot_R4_Sonoftheboss_20260131_NEXBET","track":"Ascot","race_num":4,"horse_name":"Sonoftheboss","horse_num":1,"price":5.0,"units":0.06,"rsi":86,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-31T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Fannie Bay_R1_Rock Revolution_20260131_NEXSNIPE","track":"Fannie Bay","race_num":1,"horse_name":"Rock Revolution","horse_num":1,"price":6.0,"units":0.16,"rsi":98,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-01-31T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Fannie Bay_R1_Rock Revolution_20260131_NEXBET","track":"Fannie Bay","race_num":1,"horse_name":"Rock Revolution","horse_num":1,"price":6.0,"units":0.16,"rsi":98,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-31T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Fannie Bay_R5_Bruno Bruno_20260131_NEXBET","track":"Fannie Bay","race_num":5,"horse_name":"Bruno Bruno","horse_num":2,"price":6.0,"units":0.04,"rsi":84,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-01-31T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Morphettville Parks_R3_Cielao_20260131_NEXBET","track":"Morphettville Parks","race_num":3,"horse_name":"Cielao","horse_num":7,"price":4.6,"units":0.01,"rsi":73,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-01-31T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Strathalbyn_R2_Tenterk_20260201_NEXSNIPE","track":"Strathalbyn","race_num":2,"horse_name":"Tenterk","horse_num":4,"price":5.5,"units":0.14,"rsi":99,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-02-01T13:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Strathalbyn_R2_Tenterk_20260201_NEXBET","track":"Strathalbyn","race_num":2,"horse_name":"Tenterk","horse_num":4,"price":5.5,"units":0.15,"rsi":99,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-01T13:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Strathalbyn_R4_Chartin_20260201_NEXBET","track":"Strathalbyn","race_num":4,"horse_name":"Chartin","horse_num":8,"price":4.0,"units":0.01,"rsi":73,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-01T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":10,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Sapphire Coast_R1_Falcon Gold_20260201_NEXSNIPE","track":"Sapphire Coast","race_num":1,"horse_name":"Falcon Gold","horse_num":2,"price":5.5,"units":0.03,"rsi":84,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-02-01T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Sapphire Coast_R1_Falcon Gold_20260201_NEXBET","track":"Sapphire Coast","race_num":1,"horse_name":"Falcon Gold","horse_num":2,"price":5.5,"units":0.05,"rsi":84,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-01T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Sapphire Coast_R3_Jazz All Knight_20260201_NEXBET","track":"Sapphire Coast","race_num":3,"horse_name":"Jazz All Knight","horse_num":3,"price":3.2,"units":0.04,"rsi":78,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-01T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Sapphire Coast_R6_Cougars_20260201_NEXSNIPE","track":"Sapphire Coast","race_num":6,"horse_name":"Cougars","horse_num":9,"price":2.8,"units":0.11,"rsi":91,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-02-01T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":11,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Sapphire Coast_R6_Cougars_20260201_NEXBET","track":"Sapphire Coast","race_num":6,"horse_name":"Cougars","horse_num":9,"price":2.8,"units":0.13,"rsi":91,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-01T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":11,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Beaumont_R1_Golden Smile_20260202_NEXSNIPE","track":"Beaumont","race_num":1,"horse_name":"Golden Smile","horse_num":3,"price":3.0,"units":0.12,"rsi":90,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-02-02T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Beaumont_R1_Golden Smile_20260202_NEXBET","track":"Beaumont","race_num":1,"horse_name":"Golden Smile","horse_num":3,"price":3.0,"units":0.13,"rsi":90,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-02T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Beaumont_R5_Ensign Parker_20260202_NEXBET","track":"Beaumont","race_num":5,"horse_name":"Ensign Parker","horse_num":2,"price":5.5,"units":0.04,"rsi":80,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-02T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Beaumont_R6_Issy\'s Star_20260202_NEXBET","track":"Beaumont","race_num":6,"horse_name":"Issy\'s Star","horse_num":7,"price":7.0,"units":0.03,"rsi":78,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-02T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Grafton_R4_Pixie Hallow_20260203_NEXBET","track":"Grafton","race_num":4,"horse_name":"Pixie Hallow","horse_num":1,"price":6.0,"units":0.02,"rsi":75,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-02-03T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Warwick Farm_R1_Feminino_20260204_NEXBET","track":"Warwick Farm","race_num":1,"horse_name":"Feminino","horse_num":7,"price":4.4,"units":0.01,"rsi":75,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-04T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Eagle Farm_R2_Provance_20260204_NEXBET","track":"Eagle Farm","race_num":2,"horse_name":"Provance","horse_num":6,"price":2.7,"units":0.11,"rsi":90,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-04T13:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Eagle Farm_R7_Backstage_20260204_NEXBET","track":"Eagle Farm","race_num":7,"horse_name":"Backstage","horse_num":1,"price":6.0,"units":0.1,"rsi":90,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-04T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Eagle Farm_R8_Simply Excels_20260204_NEXBET","track":"Eagle Farm","race_num":8,"horse_name":"Simply Excels","horse_num":1,"price":4.4,"units":0.01,"rsi":72,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-04T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":6,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ascot_R3_Cannykev_20260204_NEXSNIPE","track":"Ascot","race_num":3,"horse_name":"Cannykev","horse_num":2,"price":2.5,"units":0.09,"rsi":90,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-02-04T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ascot_R3_Cannykev_20260204_NEXBET","track":"Ascot","race_num":3,"horse_name":"Cannykev","horse_num":2,"price":2.5,"units":0.12,"rsi":90,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-04T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Murray Bridge GH_R6_Magic Princess_20260204_NEXBET","track":"Murray Bridge GH","race_num":6,"horse_name":"Magic Princess","horse_num":7,"price":6.0,"units":0.04,"rsi":82,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-04T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Albury_R4_Dantains Prize_20260205_NEXSNIPE","track":"Albury","race_num":4,"horse_name":"Dantains Prize","horse_num":11,"price":5.0,"units":0.12,"rsi":97,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-02-05T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Albury_R4_Dantains Prize_20260205_NEXBET","track":"Albury","race_num":4,"horse_name":"Dantains Prize","horse_num":11,"price":5.0,"units":0.14,"rsi":97,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-05T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Albury_R8_Hellberg_20260205_NEXSNIPE","track":"Albury","race_num":8,"horse_name":"Hellberg","horse_num":1,"price":5.0,"units":0.03,"rsi":81,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-02-05T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":14,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Albury_R8_Hellberg_20260205_NEXBET","track":"Albury","race_num":8,"horse_name":"Hellberg","horse_num":1,"price":5.0,"units":0.04,"rsi":81,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-05T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":14,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Geraldton_R6_Sky River_20260205_NEXSNIPE","track":"Geraldton","race_num":6,"horse_name":"Sky River","horse_num":8,"price":4.6,"units":0.08,"rsi":88,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-02-05T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Geraldton_R6_Sky River_20260205_NEXBET","track":"Geraldton","race_num":6,"horse_name":"Sky River","horse_num":8,"price":4.6,"units":0.09,"rsi":88,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-05T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Pakenham_R7_Ka Ying Cheer_20260205_NEXSNIPE","track":"Pakenham","race_num":7,"horse_name":"Ka Ying Cheer","horse_num":1,"price":6.0,"units":0.1,"rsi":90,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-02-05T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Pakenham_R7_Ka Ying Cheer_20260205_NEXBET","track":"Pakenham","race_num":7,"horse_name":"Ka Ying Cheer","horse_num":1,"price":6.0,"units":0.1,"rsi":90,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-05T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Walcha_R4_Winged_20260206_NEXSNIPE","track":"Walcha","race_num":4,"horse_name":"Winged","horse_num":1,"price":4.0,"units":0.02,"rsi":80,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-02-06T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Walcha_R4_Winged_20260206_NEXBET","track":"Walcha","race_num":4,"horse_name":"Winged","horse_num":1,"price":4.0,"units":0.03,"rsi":80,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-06T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Walcha_R5_Rivkin_20260206_NEXBET","track":"Walcha","race_num":5,"horse_name":"Rivkin","horse_num":1,"price":5.0,"units":0.05,"rsi":88,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-06T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Beaudesert_R3_Wimoweh_20260206_NEXBET","track":"Beaudesert","race_num":3,"horse_name":"Wimoweh","horse_num":6,"price":3.3,"units":0.02,"rsi":75,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-06T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Beaudesert_R6_Divine Source_20260206_NEXBET","track":"Beaudesert","race_num":6,"horse_name":"Divine Source","horse_num":4,"price":3.0,"units":0.01,"rsi":73,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-06T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Colac_R5_My Angel Shell_20260206_NEXBET","track":"Colac","race_num":5,"horse_name":"My Angel Shell","horse_num":6,"price":4.8,"units":0.03,"rsi":78,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-06T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":8,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Cranbourne_R7_Itsukushima_20260206_NEXSNIPE","track":"Cranbourne","race_num":7,"horse_name":"Itsukushima","horse_num":2,"price":4.8,"units":0.08,"rsi":88,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-02-06T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Cranbourne_R7_Itsukushima_20260206_NEXBET","track":"Cranbourne","race_num":7,"horse_name":"Itsukushima","horse_num":2,"price":4.8,"units":0.09,"rsi":88,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-06T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Cranbourne_R4_Port Albert_20260206_NEXSNIPE","track":"Cranbourne","race_num":4,"horse_name":"Port Albert","horse_num":2,"price":5.5,"units":0.02,"rsi":80,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-02-06T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Cranbourne_R4_Port Albert_20260206_NEXBET","track":"Cranbourne","race_num":4,"horse_name":"Port Albert","horse_num":2,"price":5.5,"units":0.04,"rsi":80,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-06T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Hobart_R7_Cripps_20260206_NEXSNIPE","track":"Hobart","race_num":7,"horse_name":"Cripps","horse_num":1,"price":2.5,"units":0.11,"rsi":90,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-02-06T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Hobart_R7_Cripps_20260206_NEXBET","track":"Hobart","race_num":7,"horse_name":"Cripps","horse_num":1,"price":2.5,"units":0.12,"rsi":90,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-06T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Tumut_R3_Pretty Penguin_20260207_NEXBET","track":"Tumut","race_num":3,"horse_name":"Pretty Penguin","horse_num":3,"price":4.6,"units":0.06,"rsi":87,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-02-07T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Tumut_R6_Dream Inherit_20260207_NEXSNIPE","track":"Tumut","race_num":6,"horse_name":"Dream Inherit","horse_num":2,"price":5.5,"units":0.04,"rsi":80,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-02-07T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Tumut_R6_Dream Inherit_20260207_NEXBET","track":"Tumut","race_num":6,"horse_name":"Dream Inherit","horse_num":2,"price":5.5,"units":0.04,"rsi":80,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-07T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Kembla Grange_R6_Ishikari_20260207_NEXSNIPE","track":"Kembla Grange","race_num":6,"horse_name":"Ishikari","horse_num":5,"price":6.5,"units":0.08,"rsi":89,"market_rank":5,"bet_type":"NEX SNIPE","race_time":"2026-02-07T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Kembla Grange_R6_Ishikari_20260207_NEXBET","track":"Kembla Grange","race_num":6,"horse_name":"Ishikari","horse_num":5,"price":6.5,"units":0.09,"rsi":89,"market_rank":5,"bet_type":"NEX BET","race_time":"2026-02-07T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Kembla Grange_R7_Okami Star_20260207_NEXBET","track":"Kembla Grange","race_num":7,"horse_name":"Okami Star","horse_num":15,"price":4.6,"units":0.03,"rsi":78,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-07T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Toowoomba_R2_Snitzond_20260207_NEXBET","track":"Toowoomba","race_num":2,"horse_name":"Snitzond","horse_num":3,"price":4.0,"units":0.02,"rsi":76,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-07T13:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Caulfield_R2_Make It Sweet_20260207_NEXBET","track":"Caulfield","race_num":2,"horse_name":"Make It Sweet","horse_num":4,"price":7.5,"units":0.03,"rsi":83,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-02-07T13:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":5,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Caulfield_R8_Signature Scent_20260207_NEXBET","track":"Caulfield","race_num":8,"horse_name":"Signature Scent","horse_num":4,"price":5.5,"units":0.09,"rsi":90,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-07T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":5,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ascot_R1_Sound Of Speed_20260207_NEXBET","track":"Ascot","race_num":1,"horse_name":"Sound Of Speed","horse_num":2,"price":2.8,"units":0.19,"rsi":100,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-07T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Sunshine Coast_R8_Ambassadors_20260208_NEXBET","track":"Sunshine Coast","race_num":8,"horse_name":"Ambassadors","horse_num":8,"price":7.0,"units":0.02,"rsi":78,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-08T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":7,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ararat_R4_Whistler Girl_20260208_NEXBET","track":"Ararat","race_num":4,"horse_name":"Whistler Girl","horse_num":5,"price":5.0,"units":0.03,"rsi":78,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-08T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":8,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Wangaratta_R7_Rumours Abound_20260208_NEXBET","track":"Wangaratta","race_num":7,"horse_name":"Rumours Abound","horse_num":4,"price":2.5,"units":0.08,"rsi":83,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-08T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Naracoorte_R8_Wichitall_20260208_NEXBET","track":"Naracoorte","race_num":8,"horse_name":"Wichitall","horse_num":2,"price":4.4,"units":0.08,"rsi":85,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-08T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Hobart_R9_Ziryab_20260208_NEXBET","track":"Hobart","race_num":9,"horse_name":"Ziryab","horse_num":8,"price":3.2,"units":0.04,"rsi":78,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-08T16:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Mt Barker_R5_Queen Of Hawks_20260208_NEXBET","track":"Mt Barker","race_num":5,"horse_name":"Queen Of Hawks","horse_num":4,"price":2.8,"units":0.02,"rsi":74,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-08T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Mt Barker_R3_Vomo Island_20260208_NEXSNIPE","track":"Mt Barker","race_num":3,"horse_name":"Vomo Island","horse_num":1,"price":3.4,"units":0.07,"rsi":85,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-02-08T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":8,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Mt Barker_R3_Vomo Island_20260208_NEXBET","track":"Mt Barker","race_num":3,"horse_name":"Vomo Island","horse_num":1,"price":3.4,"units":0.09,"rsi":85,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-08T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":8,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Mt Barker_R7_Storm Commander_20260208_NEXBET","track":"Mt Barker","race_num":7,"horse_name":"Storm Commander","horse_num":5,"price":4.2,"units":0.02,"rsi":76,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-08T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Muswellbrook_R7_Yes Yes Boss_20260209_NEXBET","track":"Muswellbrook","race_num":7,"horse_name":"Yes Yes Boss","horse_num":11,"price":5.0,"units":0.02,"rsi":78,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-09T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Muswellbrook_R4_Miss Rebel_20260209_NEXBET","track":"Muswellbrook","race_num":4,"horse_name":"Miss Rebel","horse_num":6,"price":2.7,"units":0.12,"rsi":90,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-09T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Muswellbrook_R6_Vicious Rumour_20260209_NEXBET","track":"Muswellbrook","race_num":6,"horse_name":"Vicious Rumour","horse_num":7,"price":2.7,"units":0.1,"rsi":86,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-09T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Wyong_R7_Hydrometer_20260210_NEXBET","track":"Wyong","race_num":7,"horse_name":"Hydrometer","horse_num":3,"price":2.6,"units":0.01,"rsi":72,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-10T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":10,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Wyong_R6_Apollo Ridge_20260210_NEXBET","track":"Wyong","race_num":6,"horse_name":"Apollo Ridge","horse_num":4,"price":3.6,"units":0.01,"rsi":74,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-10T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Lismore_R5_She\'s Enuff_20260210_NEXSNIPE","track":"Lismore","race_num":5,"horse_name":"She\'s Enuff","horse_num":9,"price":5.0,"units":0.05,"rsi":82,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-02-10T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Lismore_R5_She\'s Enuff_20260210_NEXBET","track":"Lismore","race_num":5,"horse_name":"She\'s Enuff","horse_num":9,"price":5.0,"units":0.06,"rsi":82,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-10T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Lismore_R7_All Too Foxy_20260210_NEXBET","track":"Lismore","race_num":7,"horse_name":"All Too Foxy","horse_num":9,"price":6.5,"units":0.11,"rsi":92,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-10T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Gatton_R7_Clearly George_20260210_NEXSNIPE","track":"Gatton","race_num":7,"horse_name":"Clearly George","horse_num":3,"price":4.6,"units":0.07,"rsi":89,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-02-10T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Gatton_R7_Clearly George_20260210_NEXBET","track":"Gatton","race_num":7,"horse_name":"Clearly George","horse_num":3,"price":4.6,"units":0.1,"rsi":89,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-10T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Kyneton_R6_The Arrow_20260210_NEXBET","track":"Kyneton","race_num":6,"horse_name":"The Arrow","horse_num":7,"price":6.5,"units":0.05,"rsi":82,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-02-10T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Doomben_R3_Meadowbrook_20260211_NEXSNIPE","track":"Doomben","race_num":3,"horse_name":"Meadowbrook","horse_num":7,"price":4.8,"units":0.03,"rsi":82,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-02-11T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Doomben_R3_Meadowbrook_20260211_NEXBET","track":"Doomben","race_num":3,"horse_name":"Meadowbrook","horse_num":7,"price":4.8,"units":0.05,"rsi":82,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-11T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Belmont Park_R3_Stylin\'_20260211_NEXSNIPE","track":"Belmont Park","race_num":3,"horse_name":"Stylin\'","horse_num":10,"price":8.0,"units":0.02,"rsi":80,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-02-11T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Belmont Park_R3_Stylin\'_20260211_NEXBET","track":"Belmont Park","race_num":3,"horse_name":"Stylin\'","horse_num":10,"price":8.0,"units":0.03,"rsi":80,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-11T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Goulburn_R6_Burrowa_20260212_NEXSNIPE","track":"Goulburn","race_num":6,"horse_name":"Burrowa","horse_num":4,"price":8.0,"units":0.11,"rsi":93,"market_rank":4,"bet_type":"NEX SNIPE","race_time":"2026-02-12T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Goulburn_R6_Burrowa_20260212_NEXBET","track":"Goulburn","race_num":6,"horse_name":"Burrowa","horse_num":4,"price":8.0,"units":0.12,"rsi":93,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-02-12T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Taree_R5_Dwayne_20260213_NEXSNIPE","track":"Taree","race_num":5,"horse_name":"Dwayne","horse_num":2,"price":2.7,"units":0.03,"rsi":80,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-02-13T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Taree_R5_Dwayne_20260213_NEXBET","track":"Taree","race_num":5,"horse_name":"Dwayne","horse_num":2,"price":2.7,"units":0.05,"rsi":80,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-13T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Taree_R7_Diamondsaremio_20260213_NEXBET","track":"Taree","race_num":7,"horse_name":"Diamondsaremio","horse_num":5,"price":5.0,"units":0.05,"rsi":87,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-13T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Canterbury_R5_Shalaa Gold_20260213_NEXBET","track":"Canterbury","race_num":5,"horse_name":"Shalaa Gold","horse_num":3,"price":6.5,"units":0.02,"rsi":76,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-02-13T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":10,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Clare_R4_Crown And Anchor_20260213_NEXBET","track":"Clare","race_num":4,"horse_name":"Crown And Anchor","horse_num":6,"price":5.5,"units":0.02,"rsi":75,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-13T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Clare_R5_Strawberry Swing_20260213_NEXBET","track":"Clare","race_num":5,"horse_name":"Strawberry Swing","horse_num":3,"price":5.5,"units":0.02,"rsi":75,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-13T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Clare_R6_Real Valentia_20260213_NEXBET","track":"Clare","race_num":6,"horse_name":"Real Valentia","horse_num":5,"price":3.4,"units":0.02,"rsi":77,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-13T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Esperance_R5_Swift Streaker_20260213_NEXSNIPE","track":"Esperance","race_num":5,"horse_name":"Swift Streaker","horse_num":3,"price":3.3,"units":0.04,"rsi":80,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-02-13T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":9,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Esperance_R5_Swift Streaker_20260213_NEXBET","track":"Esperance","race_num":5,"horse_name":"Swift Streaker","horse_num":3,"price":3.3,"units":0.05,"rsi":80,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-13T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":9,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Esperance_R7_Wild Imagination_20260213_NEXBET","track":"Esperance","race_num":7,"horse_name":"Wild Imagination","horse_num":1,"price":4.4,"units":0.06,"rsi":82,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-13T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Newcastle_R5_One Destiny_20260214_NEXBET","track":"Newcastle","race_num":5,"horse_name":"One Destiny","horse_num":2,"price":6.0,"units":0.06,"rsi":88,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-14T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Newcastle_R4_The Magic Man_20260214_NEXSNIPE","track":"Newcastle","race_num":4,"horse_name":"The Magic Man","horse_num":5,"price":4.8,"units":0.09,"rsi":92,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-02-14T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Newcastle_R4_The Magic Man_20260214_NEXBET","track":"Newcastle","race_num":4,"horse_name":"The Magic Man","horse_num":5,"price":4.8,"units":0.11,"rsi":92,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-14T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Newcastle_R3_Velaris_20260214_NEXSNIPE","track":"Newcastle","race_num":3,"horse_name":"Velaris","horse_num":3,"price":7.5,"units":0.11,"rsi":93,"market_rank":4,"bet_type":"NEX SNIPE","race_time":"2026-02-14T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Newcastle_R3_Velaris_20260214_NEXBET","track":"Newcastle","race_num":3,"horse_name":"Velaris","horse_num":3,"price":7.5,"units":0.12,"rsi":93,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-02-14T13:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Randwick_R6_Savvy Hallie_20260214_NEXBET","track":"Randwick","race_num":6,"horse_name":"Savvy Hallie","horse_num":2,"price":3.7,"units":0.03,"rsi":80,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-14T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Dalby_R5_Reggae Fire_20260214_NEXBET","track":"Dalby","race_num":5,"horse_name":"Reggae Fire","horse_num":2,"price":6.0,"units":0.02,"rsi":75,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-02-14T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Dalby_R4_Mr Wandji_20260214_NEXBET","track":"Dalby","race_num":4,"horse_name":"Mr Wandji","horse_num":2,"price":2.7,"units":0.01,"rsi":72,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-14T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Eagle Farm_R6_North Pole_20260214_NEXSNIPE","track":"Eagle Farm","race_num":6,"horse_name":"North Pole","horse_num":2,"price":2.6,"units":0.08,"rsi":87,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-02-14T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Eagle Farm_R6_North Pole_20260214_NEXBET","track":"Eagle Farm","race_num":6,"horse_name":"North Pole","horse_num":2,"price":2.6,"units":0.1,"rsi":87,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-14T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Eagle Farm_R10_Facundo_20260214_NEXBET","track":"Eagle Farm","race_num":10,"horse_name":"Facundo","horse_num":13,"price":6.0,"units":0.07,"rsi":90,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-14T17:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":6,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ballarat_R6_Subtle Power_20260214_NEXBET","track":"Ballarat","race_num":6,"horse_name":"Subtle Power","horse_num":11,"price":3.6,"units":0.05,"rsi":82,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-14T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Pinjarra_R5_Oisin_20260214_NEXSNIPE","track":"Pinjarra","race_num":5,"horse_name":"Oisin","horse_num":3,"price":2.8,"units":0.12,"rsi":90,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-02-14T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Pinjarra_R5_Oisin_20260214_NEXBET","track":"Pinjarra","race_num":5,"horse_name":"Oisin","horse_num":3,"price":2.8,"units":0.13,"rsi":90,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-14T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Pinjarra_R6_Golden Vale_20260214_NEXBET","track":"Pinjarra","race_num":6,"horse_name":"Golden Vale","horse_num":1,"price":6.0,"units":0.01,"rsi":73,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-14T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Pinjarra_R8_Twisted Steel_20260214_NEXSNIPE","track":"Pinjarra","race_num":8,"horse_name":"Twisted Steel","horse_num":3,"price":2.5,"units":0.07,"rsi":86,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-02-14T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Pinjarra_R8_Twisted Steel_20260214_NEXBET","track":"Pinjarra","race_num":8,"horse_name":"Twisted Steel","horse_num":3,"price":2.5,"units":0.09,"rsi":86,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-14T16:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Fannie Bay_R5_Stormfront_20260214_NEXSNIPE","track":"Fannie Bay","race_num":5,"horse_name":"Stormfront","horse_num":5,"price":4.6,"units":0.08,"rsi":88,"market_rank":3,"bet_type":"NEX SNIPE","race_time":"2026-02-14T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Fannie Bay_R5_Stormfront_20260214_NEXBET","track":"Fannie Bay","race_num":5,"horse_name":"Stormfront","horse_num":5,"price":4.6,"units":0.09,"rsi":88,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-14T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Morphettville Parks_R7_Path To Profit_20260214_NEXSNIPE","track":"Morphettville Parks","race_num":7,"horse_name":"Path To Profit","horse_num":13,"price":4.8,"units":0.02,"rsi":80,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-02-14T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":8,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Morphettville Parks_R7_Path To Profit_20260214_NEXBET","track":"Morphettville Parks","race_num":7,"horse_name":"Path To Profit","horse_num":13,"price":4.8,"units":0.03,"rsi":80,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-14T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":8,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Dubbo_R5_Brutal Love_20260215_NEXBET","track":"Dubbo","race_num":5,"horse_name":"Brutal Love","horse_num":4,"price":2.7,"units":0.2,"rsi":98,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-15T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Coffs Harbour_R4_Personal Space_20260215_NEXBET","track":"Coffs Harbour","race_num":4,"horse_name":"Personal Space","horse_num":9,"price":6.5,"units":0.07,"rsi":90,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-15T14:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":3,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Coffs Harbour_R6_Kingdom Undersiege_20260215_NEXBET","track":"Coffs Harbour","race_num":6,"horse_name":"Kingdom Undersiege","horse_num":3,"price":4.2,"units":0.03,"rsi":78,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-15T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":7,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Hobart_R5_Material Madam_20260215_NEXBET","track":"Hobart","race_num":5,"horse_name":"Material Madam","horse_num":2,"price":4.6,"units":0.07,"rsi":86,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-15T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ascot_R7_Mistress Of War_20260215_NEXSNIPE","track":"Ascot","race_num":7,"horse_name":"Mistress Of War","horse_num":3,"price":3.3,"units":0.09,"rsi":87,"market_rank":1,"bet_type":"NEX SNIPE","race_time":"2026-02-15T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Ascot_R7_Mistress Of War_20260215_NEXBET","track":"Ascot","race_num":7,"horse_name":"Mistress Of War","horse_num":3,"price":3.3,"units":0.1,"rsi":87,"market_rank":1,"bet_type":"NEX BET","race_time":"2026-02-15T15:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Cairns_R5_Parch_20260216_NEXSNIPE","track":"Cairns","race_num":5,"horse_name":"Parch","horse_num":1,"price":5.5,"units":0.03,"rsi":80,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-02-16T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Cairns_R5_Parch_20260216_NEXBET","track":"Cairns","race_num":5,"horse_name":"Parch","horse_num":1,"price":5.5,"units":0.04,"rsi":80,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-16T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":4,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Kembla Grange_R6_Satness_20260217_NEXBET","track":"Kembla Grange","race_num":6,"horse_name":"Satness","horse_num":4,"price":5.5,"units":0.01,"rsi":74,"market_rank":4,"bet_type":"NEX BET","race_time":"2026-02-17T15:00:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Rockhampton_R5_Henry\'s Blade_20260217_NEXBET","track":"Rockhampton","race_num":5,"horse_name":"Henry\'s Blade","horse_num":2,"price":4.6,"units":0.09,"rsi":90,"market_rank":3,"bet_type":"NEX BET","race_time":"2026-02-17T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Warwick Farm_R5_Lancelot Du Lac_20260218_NEXBET","track":"Warwick Farm","race_num":5,"horse_name":"Lancelot Du Lac","horse_num":2,"price":2.8,"units":0.01,"rsi":72,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-18T14:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"loss","finishing_position":2,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Kilcoy_R1_Betterindanude_20260218_NEXSNIPE","track":"Kilcoy","race_num":1,"horse_name":"Betterindanude","horse_num":1,"price":3.5,"units":0.04,"rsi":85,"market_rank":2,"bet_type":"NEX SNIPE","race_time":"2026-02-18T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"},{"id":"Kilcoy_R1_Betterindanude_20260218_NEXBET","track":"Kilcoy","race_num":1,"horse_name":"Betterindanude","horse_num":1,"price":3.5,"units":0.06,"rsi":85,"market_rank":2,"bet_type":"NEX BET","race_time":"2026-02-18T12:30:00+11:00","recorded_at":"2026-02-18T13:14:13.577367+00:00","result":"win","finishing_position":1,"settled_at":"2026-02-18T13:14:13.577367+00:00"}]')



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

        # Merge built-in backtest seed (233 bets, Jan 18–Feb 18 2026)
        existing_ids = {b.get("id") for b in bets}
        new_bets = [b for b in _BACKTEST_SEED if b.get("id") not in existing_ids]
        if new_bets:
            bets.extend(new_bets)
            print(f"  Merged {len(new_bets)} backtest bets from built-in seed")
            self.bets = bets
            self._save_bets()

        return bets

    def _save_bets(self):
        """Save bets to JSON file"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.bets, f, indent=2, default=str)
        except IOError as e:
            print(f"Error saving bets: {e}")

    def record_bet(self, track: str, race_num: int, horse_name: str, horse_num: int,
                   price: float, units: float, rsi: int,
                   race_time: datetime, market_rank: int = 999, bet_type: str = "NEX SNIPE") -> str:
        """Record a new bet and return its ID"""
        bet_id = f"{track}_R{race_num}_{horse_name}_{race_time.strftime('%Y%m%d_%H%M')}"

        bet = {
            "id": bet_id,
            "track": track,
            "race_num": race_num,
            "horse_name": horse_name,
            "horse_num": horse_num,
            "price": price,
            "units": units,
            "rsi": rsi,

            "market_rank": market_rank,
            "bet_type": bet_type,  # NEX SNIPE or NEX BET
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

    def calculate_stats(self, bets: List[Dict], market_rank_filter: int = None, bet_type_filter: str = None) -> Dict:
        """Calculate statistics for a list of bets"""
        if market_rank_filter is not None:
            bets = [b for b in bets if b.get("market_rank") == market_rank_filter]

        if bet_type_filter is not None:
            # Handle old bets without bet_type field (backward compatibility)
            filtered_bets = []
            for b in bets:
                bet_type = b.get("bet_type")

                # Infer bet_type for old bets without the field
                if bet_type is None:
                    bet_type = "NEX SNIPE" if b.get("is_tracked", False) else "NEX BET"

                if bet_type == bet_type_filter:
                    filtered_bets.append(b)
            bets = filtered_bets

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
                 units: float, rsi: int, market_rank: int = 999,
                 bet_type: str = "NEX SNIPE"):
        """Send a formatted tip to Discord with retry logic"""
        if not self.bot_token or not self.channel_id:
            return False

        # Set colors and emojis based on bet type
        if bet_type == "NEX BET":
            color = 0x00D4FF  # Cyan — high volume PF system
            emoji = "💠"
        else:  # NEX SNIPE
            color = 0xFFD700  # Gold — sniper PF system
            emoji = "🎯"
        rating_label = "PF Score"

        title = f"{emoji} {bet_type} | {track} R{race_num}"

        fields = [
            {"name": "⏰ Race Time", "value": race_time, "inline": True},
            {"name": "📏 Distance", "value": f"{distance}m", "inline": True},
            {"name": "🌿 Surface", "value": surface, "inline": True},
            {"name": "🐴 Selection", "value": f"**{horse_num}. {horse_name}**", "inline": False},
            {"name": "💰 Odds", "value": f"${price:.2f}", "inline": True},
            {"name": "📊 Units", "value": f"{units:.2f}u", "inline": True},
            {"name": f"📈 {rating_label}", "value": f"{rsi}", "inline": True},
        ]

        # Add market rank for all bet types
        fields.append({"name": "🏆 Market Rank", "value": f"Rank {market_rank}", "inline": True})

        footer_text = f"Horse Tipper | {emoji} {bet_type}"

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
    def send_results_embed(self, period: str, overall_stats: Dict, snipe_stats: Dict = None, nex_bet_stats: Dict = None):
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

        # NEX SNIPE section
        if snipe_stats and snipe_stats["total_bets"] > 0:
            fields.append({"name": "🎯 NEX SNIPE (PF Sniper)", "value": "━━━━━━━━━━━━━━━━━━━━", "inline": False})
            fields.extend([
                {"name": "Bets", "value": str(snipe_stats["total_bets"]), "inline": True},
                {"name": "Wins", "value": f"{snipe_stats['wins']} ({snipe_stats['win_rate']}%)", "inline": True},
                {"name": "P/L", "value": f"{snipe_stats['profit']:+.2f}u", "inline": True},
                {"name": "ROI", "value": f"{snipe_stats['roi']:+.1f}%", "inline": True},
                {"name": "Avg Odds", "value": f"${snipe_stats['avg_odds']:.2f}", "inline": True},
                {"name": "\u200b", "value": "\u200b", "inline": True},
            ])

        # NEX BET section
        if nex_bet_stats and nex_bet_stats["total_bets"] > 0:
            fields.append({"name": "💠 NEX BET (PF Volume)", "value": "━━━━━━━━━━━━━━━━━━━━", "inline": False})
            fields.extend([
                {"name": "Bets", "value": str(nex_bet_stats["total_bets"]), "inline": True},
                {"name": "Wins", "value": f"{nex_bet_stats['wins']} ({nex_bet_stats['win_rate']}%)", "inline": True},
                {"name": "P/L", "value": f"{nex_bet_stats['profit']:+.2f}u", "inline": True},
                {"name": "ROI", "value": f"{nex_bet_stats['roi']:+.1f}%", "inline": True},
                {"name": "Avg Odds", "value": f"${nex_bet_stats['avg_odds']:.2f}", "inline": True},
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
            "footer": {"text": f"Horse Tipper | 🎯 NEX SNIPE • 💠 NEX BET • Generated {datetime.now(AEDT).strftime('%H:%M')}"}
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
        "!wipe": "wipe",      # Clear all bets and reload backtest seed
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

                # Debug: log if we can't read messages
                if messages is None or len(messages) == 0:
                    # Only print this once every 30 seconds to avoid spam
                    if not hasattr(self, '_last_warning') or time.time() - self._last_warning > 30:
                        print("⚠ Discord command handler: No messages received (check bot permissions)")
                        self._last_warning = time.time()

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
                        elif command_type == "wipe":
                            self._send_wipe()
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

        # If no bets, send a simple message
        if not bets:
            period_names = {
                "daily": "today",
                "weekly": "this week",
                "monthly": "this month",
                "yearly": "this year",
                "lifetime": "all time"
            }
            period_name = period_names.get(period, period)
            self.discord.send_message(f"📊 No bets recorded {period_name}.")
            print(f"📊 Sent '{period}' results to Discord (no bets)")
            return

        # Calculate stats for each bet type
        nex_snipe_stats = self.bet_tracker.calculate_stats(bets, bet_type_filter="NEX SNIPE")
        nex_bet_stats   = self.bet_tracker.calculate_stats(bets, bet_type_filter="NEX BET")
        overall_stats   = self.bet_tracker.calculate_stats(bets)

        self.discord.send_results_embed(period, overall_stats,
                                        snipe_stats=nex_snipe_stats, nex_bet_stats=nex_bet_stats)

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
            bet_type = bet.get("bet_type", "")
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
            bet_type = bet.get("bet_type", "")
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

**Admin:**
`!wipe` - Clear all bets and reload backtest seed

**Systems:**
🎯 **NEX SNIPE** - PF Rank ≤2, Score ≥80, op style, ps≤3 (~49% ROI, 4/day)
💠 **NEX BET** - PF Rank ≤5, Score ≥70, op style, ps≤3 (~28% ROI, 7/day)
- Stakes: Kelly × Confidence (capped at 4.0u)"""

        self.discord.send_message(help_text)

    def _send_wipe(self):
        """Clear all bets and reload from built-in backtest seed"""
        old_count = len(self.bet_tracker.bets)

        # Load seed directly from built-in constant — no file I/O needed
        self.bet_tracker.bets = list(_BACKTEST_SEED)
        self.bet_tracker._save_bets()
        new_count = len(self.bet_tracker.bets)

        self.discord.send_message(
            f"🗑️ **Tracker wiped!**\n"
            f"Removed {old_count} old bets.\n"
            f"Loaded {new_count} backtest bets (NEX SNIPE + NEX BET history)."
        )
        print(f"🗑️ Wipe: removed {old_count} bets, reloaded {new_count} from built-in seed")


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

    # Punting Form enriched data (set after PF API fetch)
    pf_score: Optional[float] = None    # pfaiScore 0-100
    pf_price: Optional[float] = None    # pfaiPrice (PF fair value)
    pf_rank: Optional[int] = None       # pfaiRank (1 = best)
    time_rank: Optional[int] = None     # timeRank (1 = fastest)
    pred_settle: Optional[int] = None   # predictedSettle (pace map settle position; ≤4 = key signal)
    value_ratio: float = 0.0            # bookie price / pfaiPrice (>1 = market generous)
    is_reliable: bool = False           # PF isReliable flag
    run_style: str = ""                 # runStyle (l/op/op_mf/mf/bm)
    tj_a2e: float = 0.0                 # trainer+jockey A2E (>1 = profitable combo)
    win_pct: float = 0.0                # career win % (≥10% = huge signal: +74% ROI)
    class_change: Optional[float] = None  # class drop: ≤0 = easier class (sniper signal)

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
                                'TRIAL' in race_class or
                                'JUMP OUT' in race_class or
                                '-TRL' in race_class or
                                race_class.endswith('TRL')):
                                print(f"    ⚠️  R{race_number}: SKIPPED (trial/jump out)")
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

                            # Check if race has real bookmaker odds (not trials with default prices)
                            # Count how many runners have actual bookmaker odds vs defaults
                            runners_with_odds = sum(1 for r in race_detail.get('runners', [])
                                                   if r.get('odds') and len(r.get('odds', [])) > 0)
                            total_runners = len(race_detail.get('runners', []))

                            if total_runners > 0 and runners_with_odds < (total_runners * 0.5):
                                print(f"    ⚠️ R{race_number}: SKIPPED (no real bookmaker odds - likely trial)")
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


class PuntingFormClient:
    """
    Client for the Punting Form API v2.
    Fetches pfaiScore, pfaiRank, timeRank, assessedPrice, runStyle,
    trainerJockey A2E and other signals for each runner.
    Returns a lookup: {track_lower: {race_no: {name_lower: {fields}}}}
    """

    PF_KEY = "c1c7caee-e27b-4e93-b41f-00904b84d333"
    BASE   = "https://api.puntingform.com.au/v2"

    def __init__(self):
        self.session = requests.Session()

    def _get(self, endpoint: str, params: Dict) -> list:
        params = dict(params)
        params["apiKey"] = self.PF_KEY
        for attempt in range(3):
            try:
                r = self.session.get(f"{self.BASE}/{endpoint}", params=params, timeout=20)
                if r.status_code == 200:
                    return r.json().get("payLoad", []) or []
                if r.status_code in (400, 404):
                    return []
            except Exception as e:
                if attempt == 2:
                    print(f"  ⚠ PF API {endpoint}: {e}")
            time.sleep(0.4)
        return []

    def get_today_data(self) -> Dict:
        """
        Fetch all PF data for today's AU TAB races.
        Returns: {track_lower: {race_no(int): {runner_name_lower: {...pf fields...}}}}
        """
        today_str = datetime.now(AEDT).strftime("%-d-%b-%Y")
        meetings_raw = self._get("form/meetingslist", {"meetingDate": today_str})

        # Filter: AU TAB only, no trials/jumps
        meetings = [m for m in (meetings_raw or [])
                    if m.get("tabMeeting")
                    and not m.get("isBarrierTrial")
                    and not m.get("isJumps")
                    and (m.get("track") or {}).get("country") == "AUS"]

        if not meetings:
            print("  ⚠ PF: No AU TAB meetings found for today")
            return {}

        print(f"  ✓ PF: {len(meetings)} AU TAB meetings")
        result: Dict[str, Dict] = {}

        for m in meetings:
            mid   = m["meetingId"]
            track = (m.get("track") or {}).get("name", "").lower()

            # Ratings
            ratings_raw = self._get("Ratings/MeetingRatings", {"meetingId": mid})
            ratings_by_id: Dict[int, Dict] = {}
            for rat in (ratings_raw or []):
                if isinstance(rat, dict) and rat.get("runnerId"):
                    try:
                        ratings_by_id[int(rat["runnerId"])] = rat
                    except (ValueError, TypeError):
                        pass

            # Speedmaps
            sm_raw = self._get("User/Speedmaps", {"meetingId": mid})
            sm_by_id: Dict[int, Dict] = {}
            for sm_race in (sm_raw or []):
                if not isinstance(sm_race, dict):
                    continue
                for item in sm_race.get("items", []):
                    if isinstance(item, dict) and item.get("runnerId"):
                        try:
                            sm_by_id[int(item["runnerId"])] = item
                        except (ValueError, TypeError):
                            pass

            # Fields (runner names per race)
            fields_raw = self._get("form/fields", {"meetingId": mid})
            if isinstance(fields_raw, dict):
                fields_races = fields_raw.get("races", [])
            elif isinstance(fields_raw, list):
                fields_races = []
                for fi in fields_raw:
                    if isinstance(fi, dict) and "races" in fi:
                        fields_races = fi["races"]
                        break
            else:
                fields_races = []

            track_data: Dict[int, Dict] = {}
            for race in fields_races:
                race_no = int(race.get("number", 0))
                race_runners: Dict[str, Dict] = {}

                for runner in race.get("runners", []):
                    rid_raw = runner.get("runnerId")
                    try:
                        rid = int(rid_raw)
                    except (TypeError, ValueError):
                        continue

                    rat  = ratings_by_id.get(rid, {})
                    smap = sm_by_id.get(rid, {})

                    name = (runner.get("name") or "").lower().strip()
                    if not name:
                        continue

                    # Build A2E values
                    tj_career = (runner.get("trainerJockeyA2E_Career") or {})
                    tj_100    = (runner.get("trainerJockeyA2E_Last100") or {})
                    tj_a2e    = float(tj_100.get("a2E") or tj_career.get("a2E") or 0.0)

                    pf_price_raw = rat.get("pfaiPrice") or 0.0
                    try:
                        pf_price_val = float(pf_price_raw)
                    except (ValueError, TypeError):
                        pf_price_val = 0.0

                    cc_raw = runner.get("classChange")

                    race_runners[name] = {
                        "pfaiScore"     : rat.get("pfaiScore"),
                        "pfaiPrice"     : pf_price_val,
                        "pfaiRank"      : rat.get("pfaiRank"),
                        "timeRank"      : rat.get("timeRank"),
                        "isReliable"    : bool(rat.get("isReliable")),
                        "runStyle"      : (rat.get("runStyle") or "").strip().lower(),
                        "assessedPrice" : smap.get("assessedPrice"),
                        "predictedSettle": rat.get("predictedSettlePostion"),
                        "smSettle"      : smap.get("settle"),
                        "tj_a2e"        : tj_a2e,
                        # NEW high-value signals
                        "winPct"        : float(runner.get("winPct") or 0.0),
                        "classChange"   : float(cc_raw) if cc_raw is not None else None,
                    }

                if race_runners:
                    track_data[race_no] = race_runners

            if track_data:
                result[track] = track_data

            time.sleep(0.3)

        print(f"  ✓ PF: loaded data for {len(result)} tracks")
        return result

    @staticmethod
    def enrich_runners(races: List, pf_data: Dict) -> None:
        """
        Merge PF data into Runner objects in-place.
        Matches on track name (case-insensitive) + race number + horse name.
        """
        if not pf_data:
            return

        matched = 0
        for race in races:
            track_lower = race.track_name.lower()

            # Fuzzy track match (PF may use slightly different names)
            track_key = None
            if track_lower in pf_data:
                track_key = track_lower
            else:
                for pf_track in pf_data:
                    # Match if one contains the other (e.g. "flemington" in "flemington r1")
                    if pf_track in track_lower or track_lower in pf_track:
                        track_key = pf_track
                        break

            if not track_key:
                continue

            race_map = pf_data[track_key].get(race.race_number, {})
            if not race_map:
                continue

            for runner in race.runners:
                name_lower = runner.name.lower().strip()
                pf = race_map.get(name_lower)
                if not pf:
                    # Try partial match (first word)
                    first_word = name_lower.split()[0] if name_lower else ""
                    for pf_name, pf_val in race_map.items():
                        if first_word and pf_name.startswith(first_word):
                            pf = pf_val
                            break

                if pf:
                    if pf.get("pfaiScore") is not None:
                        try:
                            runner.pf_score = float(pf["pfaiScore"])
                        except (ValueError, TypeError):
                            pass
                    runner.pf_price = pf.get("pfaiPrice") or None
                    if pf.get("pfaiRank") is not None:
                        try:
                            runner.pf_rank = int(pf["pfaiRank"])
                        except (ValueError, TypeError):
                            pass
                    if pf.get("timeRank") is not None:
                        try:
                            runner.time_rank = int(pf["timeRank"])
                        except (ValueError, TypeError):
                            pass
                    runner.is_reliable = bool(pf.get("isReliable"))
                    # Normalize run_style: "op/mf" → "op_mf" for set membership checks
                    raw_style = (pf.get("runStyle") or "").strip()
                    runner.run_style = raw_style.replace("/", "_") if "/" in raw_style else raw_style
                    runner.tj_a2e  = float(pf.get("tj_a2e") or 0.0)
                    runner.win_pct = float(pf.get("winPct") or 0.0)
                    cc_val = pf.get("classChange")
                    runner.class_change = float(cc_val) if cc_val is not None else None
                    if pf.get("predictedSettle") is not None:
                        try:
                            runner.pred_settle = int(pf["predictedSettle"])
                        except (ValueError, TypeError):
                            pass

                    # Value ratio: bookie price / PF fair price
                    if runner.pf_price and runner.pf_price > 1.0:
                        runner.value_ratio = round(runner.price / runner.pf_price, 3)

                    matched += 1

        if matched:
            print(f"  ✓ PF: enriched {matched} runners with PF signals")


class HorseRacingAnalyst:
    """
    PRODUCTION HORSE RACING ANALYST
    PF Signal System (NEX SNIPE + NEX BET) with Full Kelly staking
    """

    # PUNTING FORM ENHANCED FILTERS — tuned from expanded 32-day backtest
    # Key discoveries (backtest_pf_maximise.py):
    #   • strict 'op' only (not op/mf) is the biggest single signal
    #   • predictedSettle ≤ 3 is a powerful clean filter
    #   • pfaiScore ≥ 80 (SN) / ≥ 70 (HV) are sweet spots
    #
    # Backtest performance by mode (32 days, clean signals):
    #   ULTRA  : +112% ROI  1.4/day  (pfRk=1, sc≥80, er≤2, ps≤3) — tiny sample, high variance
    #   SNIPER : ~+49% ROI  4.0/day  (pfRk≤2, sc≥80, ps≤3)       — practical sweet spot
    #   HIGH_VOL: +28% ROI  7.4/day  (pfRk≤5, sc≥70, ps≤3)       — max volume
    #
    # ── System mode ───────────────────────────────────────────────────────────
    # "HIGH_VOL" : 7-8 bets/day, ~28% ROI
    # "SNIPER"   : 4-5 bets/day, ~49% ROI  ← recommended
    SYSTEM_MODE  = "SNIPER"

    # ── HIGH_VOL config ───────────────────────────────────────────────────────
    # $2.50-$8, pfRk≤5, sc≥70, op_strict, rel, ps≤3
    # Backtest: +27.7% ROI, 7.4/day
    HV_MIN_PRICE   = 2.50
    HV_MAX_PRICE   = 8.00
    HV_MAX_RANK    = 5
    HV_MIN_SCORE   = 70
    HV_MAX_TR      = 99   # timeRank filter removed — hurts volume without improving ROI
    HV_MAX_SETTLE  = 3    # predictedSettle ≤ 3 — key signal
    HV_PACE_STYLES = {"op"}   # strict 'op' only — excludes op/mf hybrids
    HV_RELIABLE    = True
    HV_MIN_WIN_PCT = 5.0   # career win % ≥ 5%

    # ── SNIPER config ─────────────────────────────────────────────────────────
    # $2.50-$8, pfRk≤2, sc≥80, op_strict, rel, ps≤3, tr≤3
    # Backtest: +48.6% ROI, 4.0/day (~49% ROI sweet spot)
    SN_MIN_PRICE   = 2.50
    SN_MAX_PRICE   = 8.00
    SN_MAX_RANK    = 2
    SN_MIN_SCORE   = 80   # raised to 80 — hits the ~49% ROI sweet spot
    SN_MAX_TR      = 3
    SN_MAX_SETTLE  = 3    # predictedSettle ≤ 3 — key signal
    SN_PACE_STYLES = {"op"}
    SN_RELIABLE    = True
    SN_MIN_WIN_PCT = 5.0   # winPct ≥ 5%
    SN_MAX_CC      = 0.0   # classChange ≤ 0 (dropped class or same)

    def __init__(self):
        self.analysis_cache = {}

    def _calculate_market_rank(self, runner: Runner, race: Race) -> int:
        """Calculate horse's market rank (1 = favorite)"""
        sorted_runners = sorted(race.runners, key=lambda r: r.price)
        for rank, r in enumerate(sorted_runners, 1):
            if r.name == runner.name:
                return rank
        return 999

    def _is_tracked(self, runner: Runner, mode: str = None) -> bool:
        """
        Filter using PF signals (two modes) or market-rank fallback.

        HIGH_VOL mode: $2-$10, pfRk≤4, sc≥65, l+op, rel, ps≤4, winPct≥5%
          → backtest: +42.4% ROI at 10.3/day  (NEX BET)

        SNIPER mode: $2.50-$8, pfRk≤2, sc≥82, op, rel, ps≤4, winPct≥5%, cc≤0
          → backtest: +49% ROI at 4/day  (NEX SNIPE)

        mode parameter overrides self.SYSTEM_MODE for this call only.
        """
        pf_available = runner.pf_rank is not None
        active_mode  = mode or self.SYSTEM_MODE

        if pf_available:
            if active_mode == "SNIPER":
                # ── SNIPER ────────────────────────────────────────────────────
                if not (self.SN_MIN_PRICE <= runner.price <= self.SN_MAX_PRICE):
                    return False
                if runner.pf_rank > self.SN_MAX_RANK:
                    return False
                if runner.pf_score is not None and runner.pf_score < self.SN_MIN_SCORE:
                    return False
                if runner.time_rank is not None and runner.time_rank > self.SN_MAX_TR:
                    return False
                if self.SN_RELIABLE and not runner.is_reliable:
                    return False
                if runner.run_style and runner.run_style not in self.SN_PACE_STYLES:
                    return False
                if runner.pred_settle is not None and runner.pred_settle > self.SN_MAX_SETTLE:
                    return False
                if runner.win_pct < self.SN_MIN_WIN_PCT:
                    return False
                # classChange: must have data and be ≤ 0 (dropped class or same)
                if runner.class_change is None or runner.class_change > self.SN_MAX_CC:
                    return False
                return True

            else:
                # ── HIGH_VOL (default) ────────────────────────────────────────
                if not (self.HV_MIN_PRICE <= runner.price <= self.HV_MAX_PRICE):
                    return False
                if runner.pf_rank > self.HV_MAX_RANK:
                    return False
                if runner.pf_score is not None and runner.pf_score < self.HV_MIN_SCORE:
                    return False
                if runner.time_rank is not None and runner.time_rank > self.HV_MAX_TR:
                    return False
                if self.HV_RELIABLE and not runner.is_reliable:
                    return False
                if runner.run_style and runner.run_style not in self.HV_PACE_STYLES:
                    return False
                if runner.pred_settle is not None and runner.pred_settle > self.HV_MAX_SETTLE:
                    return False
                if runner.win_pct < self.HV_MIN_WIN_PCT:
                    return False
                return True

        return False  # No PF data available — skip runner

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
            # Get top selection based on speed rating
            selection = self._get_top_selection(race)

            if not selection:
                continue  # Skip if no selection possible

            # Calculate speed rating and Win %
            speed_rating = self._calculate_speed_rating(selection)
            win_pct = self._calculate_win_percentage(selection, speed_rating)

            # Calculate Units (Kelly Criterion based)
            units = self._calculate_units(selection, win_pct)

            # Check if this is a tracked bet (meets PF criteria)
            is_tracked = self._is_tracked(selection)

            # Format output (4 lines per race)
            # Tracked bets are marked with **bold** formatting
            if is_tracked:
                # TRACKED BET - Bold formatting
                line1 = f"**{race.track_name} - {race.race_number}**"
                line2 = f"**{race.distance}m - {race.surface}**"
                line3 = f"**{race.track_name} {race.race_number} | {selection.saddlecloth} {selection.name}**"
                line4 = f"**${selection.price:.2f} {units}u {int(speed_rating)}%** EDGE"
            else:
                # Regular bet - no bold
                line1 = f"{race.track_name} - {race.race_number}"
                line2 = f"{race.distance}m - {race.surface}"
                line3 = f"{race.track_name} {race.race_number} | {selection.saddlecloth} {selection.name}"
                line4 = f"${selection.price:.2f} {units}u {int(speed_rating)}%"

            # Add all lines for this race
            output_lines.append(line1)
            output_lines.append(line2)
            output_lines.append(line3)
            output_lines.append(line4)
            output_lines.append("")  # Blank line between races

        return "\n".join(output_lines)

    def _calculate_units(self, runner: Runner, win_pct: float, mode: str = None) -> float:
        """
        Kelly × confidence staking.

        Step 1 — Kelly fraction:
            edge = (p * b - 1) / (b - 1)
            where p = win probability, b = decimal odds

        Step 2 — Confidence multiplier (0.25 – 1.0):
            Derived from how far pfaiScore, pfaiRank, predictedSettle
            exceed their qualifying thresholds.
            • Weakest qualifying signal  → 0.25× Kelly (quarter Kelly)
            • Strongest signal (all max) → 1.0× Kelly (full Kelly)

        Cap at 4.0 units.
        """
        win_probability = win_pct / 100.0
        price = runner.price

        if win_probability <= 0 or price <= 1:
            return 0.0

        edge = (win_probability * price - 1) / (price - 1)
        if edge <= 0:
            return 0.0

        confidence = self._calculate_confidence(runner, mode) if mode else 0.5
        kelly_bet  = confidence * edge

        return round(min(kelly_bet, 4.0), 2)

    # ========================================
    # SELECTION METHODS
    # ========================================

    def _get_top_selection(self, race: Race) -> Optional[Runner]:
        """
        Get single best selection for a race based on speed rating
        Returns runner or None
        """
        if not race.runners:
            return None

        # Calculate speed rating for all runners
        scored = []
        for runner in race.runners:
            speed_rating = self._calculate_speed_rating(runner)
            scored.append({
                'runner': runner,
                'speed_rating': speed_rating
            })

        # Sort by speed rating (deterministic tie-break: lowest saddlecloth)
        scored.sort(key=lambda x: (-x['speed_rating'], x['runner'].saddlecloth))

        # Return top runner
        return scored[0]['runner']


    # ========================================
    # SCORING & ASSESSMENT FUNCTIONS
    # ========================================

    def _calculate_speed_rating(self, runner: Runner) -> int:
        """Returns PF pfaiScore (0-100), or 70 as default."""
        if runner.pf_score is not None:
            return max(0, min(100, int(runner.pf_score)))
        return 70


    def _calculate_win_percentage(self, runner: Runner, speed_rating: int) -> float:
        """
        Win probability = market implied + PF edge boost.
        Market implied (1/price) is the honest baseline.
        PF score above 70 adds a small edge on top.
        Returns percentage (0-100).
        """
        if runner.price <= 1:
            return 0.0
        # Market implied probability
        implied = (1.0 / runner.price) * 100.0
        # PF edge boost: 0% at score 70, +15% at score 100
        pf_boost = max(0.0, (speed_rating - 70) / 2.0)
        return min(85.0, implied + pf_boost)

    def _calculate_confidence(self, runner: Runner, mode: str) -> float:
        """
        Confidence multiplier (0.25 – 1.0) based on how strongly PF signals
        exceed their qualifying thresholds.

        Components (weighted):
          40% — pfaiScore  (how far above min threshold)
          35% — pfaiRank   (rank 1 = best, max_rank = worst)
          25% — predictedSettle (1 = best, 3 = just qualifying)

        Returns 0.25 (just qualifying) → 1.0 (all signals at maximum).
        """
        pf_score    = runner.pf_score   or 0
        pf_rank     = runner.pf_rank    or 99
        pred_settle = runner.pred_settle or 3

        if mode == "SNIPER":
            min_score = self.SN_MIN_SCORE   # 80
            max_rank  = self.SN_MAX_RANK    # 2
        else:  # HIGH_VOL
            min_score = self.HV_MIN_SCORE   # 70
            max_rank  = self.HV_MAX_RANK    # 5

        # Score: 0 at min_score, 1.0 at 100
        score_range = max(1, 100 - min_score)
        score_conf  = min(1.0, max(0.0, (pf_score - min_score) / score_range))

        # Rank: rank 1 = 1.0, max_rank = 0.0 (linear)
        rank_conf = max(0.0, 1.0 - (pf_rank - 1) / max(1, max_rank))

        # Settle: settle 1 = 1.0, settle 3 = 0.0 (qualifying ceiling)
        settle_conf = max(0.0, (self.SN_MAX_SETTLE + 1 - pred_settle) / self.SN_MAX_SETTLE)

        raw = 0.40 * score_conf + 0.35 * rank_conf + 0.25 * settle_conf

        # Map raw 0–1 → final 0.25–1.0 so even the weakest qualifying bet
        # gets at least quarter-Kelly
        return round(max(0.25, min(1.0, raw)), 4)





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
                for name, pos in positions.items():
                    name_normalized = normalize_name(name)

                    # Try multiple matching strategies
                    if (horse_normalized == name_normalized or
                        horse_normalized in name_normalized or
                        name_normalized in horse_normalized or
                        # Also try exact match on original names
                        horse_name.lower().strip() == name.lower().strip()):
                        position = pos
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
    discord_token_2 = os.getenv('DISCORD_TOKEN_2')
    discord_channel_2 = os.getenv('DISCORD_CHANNEL_ID_2')
    if not username or not password:
        print("Error: RACING_API_USERNAME and RACING_API_PASSWORD must be set in .env file")
        return

    print("=" * 60)
    print("HORSE TIPPER - Live Race Monitor")
    print("🎯 NEX SNIPE (~49% ROI, 4/day) | 💠 NEX BET (~28% ROI, 7/day)")
    print("PF signals: pfaiRank, pfaiScore, predictedSettle, runStyle")
    print("Outputs selections 3 minutes before race start")
    if discord_token and discord_channel:
        print("✓ Discord bot 1 enabled")
    else:
        print("⚠ No DISCORD_TOKEN/DISCORD_CHANNEL_ID set - console output only")
    if discord_token_2 and discord_channel_2:
        print("✓ Discord bot 2 enabled")
    print("=" * 60)

    # Initialize API client, Discord, and bet tracker
    api_client = RacingAPIClient(username, password)
    pf_client  = PuntingFormClient()
    analyst = create_analyst()
    discord = DiscordNotifier(discord_token, discord_channel) if discord_token and discord_channel else None
    discord2 = DiscordNotifier(discord_token_2, discord_channel_2) if discord_token_2 and discord_channel_2 else None

    bet_tracker = BetTracker()

    # Start Discord command handlers (one for each bot)
    command_handler = None
    command_handler2 = None
    if discord:
        command_handler = DiscordCommandHandler(discord, bet_tracker)
        command_handler.start()
    if discord2:
        command_handler2 = DiscordCommandHandler(discord2, bet_tracker)
        command_handler2.start()

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

    # Fetch Punting Form data and enrich runners
    print("\nFetching Punting Form signals...")
    try:
        pf_data = pf_client.get_today_data()
        if pf_data and races:
            PuntingFormClient.enrich_runners(races, pf_data)
    except Exception as e:
        pf_data = {}
        print(f"  ⚠ PF fetch failed: {e}")

    print("\nMonitoring for races starting soon... (Ctrl+C to stop)\n")

    # Track last fetch time, last settlement check, and last PF refresh
    last_fetch_time = time.time()
    last_settlement_check = time.time()
    last_pf_refresh = time.time()

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
                    # Re-enrich with existing PF data (or refreshed below)
                    if pf_data:
                        PuntingFormClient.enrich_runners(races, pf_data)
                last_fetch_time = time.time()

            # Refresh PF data every 30 minutes (ratings update as markets move)
            if time.time() - last_pf_refresh > 1800:
                try:
                    new_pf = pf_client.get_today_data()
                    if new_pf:
                        pf_data = new_pf
                        if races:
                            PuntingFormClient.enrich_runners(races, pf_data)
                except Exception as e:
                    print(f"  ⚠ PF refresh failed: {e}")
                last_pf_refresh = time.time()

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
                        # PF SYSTEMS: NEX SNIPE + NEX BET (independent)
                        # Both go to Server 1 ch1 + Server 2 ch1
                        # ========================================

                        # ── NEX SNIPE (SNIPER system, ~49% ROI, 4/day) ──────────────────
                        # Checks INDEPENDENTLY — can fire alongside NEX BET
                        sniper_candidates = []
                        for runner in race.runners:
                            if not analyst._is_tracked(runner, mode="SNIPER"):
                                continue
                            speed_rating = analyst._calculate_speed_rating(runner)
                            win_pct      = analyst._calculate_win_percentage(runner, speed_rating)
                            units        = analyst._calculate_units(runner, win_pct, mode="SNIPER")
                            market_rank  = analyst._calculate_market_rank(runner, race)
                            confidence   = analyst._calculate_confidence(runner, mode="SNIPER")
                            if units > 0:
                                sniper_candidates.append({
                                    'runner': runner,
                                    'speed_rating': speed_rating,
                                    'units': units,
                                    'market_rank': market_rank,
                                    'confidence': confidence,
                                })

                        if sniper_candidates:
                            sniper_candidates.sort(key=lambda x: (-x['speed_rating'], x['market_rank']))
                            best_sniper = sniper_candidates[0]
                            runner     = best_sniper['runner']
                            sr         = best_sniper['speed_rating']
                            units      = best_sniper['units']
                            mkt_rank   = best_sniper['market_rank']
                            conf_pct   = int(best_sniper['confidence'] * 100)

                            bet_tracker.record_bet(
                                track=race.track_name, race_num=race.race_number,
                                horse_name=runner.name, horse_num=runner.saddlecloth,
                                price=runner.price, units=units, rsi=sr,
                                race_time=race.start_time,
                                market_rank=mkt_rank, bet_type="NEX SNIPE"
                            )
                            pf_lbl = f"{runner.pf_score or sr:.0f}"
                            tip_kwargs = dict(
                                race_time=race_time_str, track=race.track_name,
                                race_num=race.race_number, distance=race.distance,
                                surface=race.surface, horse_num=runner.saddlecloth,
                                horse_name=runner.name, price=runner.price,
                                units=units, rsi=pf_lbl,
                                market_rank=mkt_rank, bet_type="NEX SNIPE"
                            )
                            if discord:
                                discord.send_tip(**tip_kwargs)
                            if discord2:
                                discord2.send_tip(**tip_kwargs)
                            print(f"\n⏰ {race_time_str} | {race.track_name} R{race.race_number} [🎯 NEX SNIPE]")
                            print(f"   {runner.saddlecloth}. {runner.name} @ ${runner.price:.2f}")
                            print(f"   {units:.2f}u | Conf {conf_pct}% | PF Score {pf_lbl} | WinPct {runner.win_pct:.0f}% | Rank {mkt_rank}")

                        # ── NEX BET (HIGH_VOL system, ~28% ROI, 7/day) ──────────────────
                        # Checks INDEPENDENTLY — can fire alongside NEX SNIPE
                        bet_candidates = []
                        for runner in race.runners:
                            if not analyst._is_tracked(runner, mode="HIGH_VOL"):
                                continue
                            speed_rating = analyst._calculate_speed_rating(runner)
                            win_pct      = analyst._calculate_win_percentage(runner, speed_rating)
                            units        = analyst._calculate_units(runner, win_pct, mode="HIGH_VOL")
                            market_rank  = analyst._calculate_market_rank(runner, race)
                            confidence   = analyst._calculate_confidence(runner, mode="HIGH_VOL")
                            if units > 0:
                                bet_candidates.append({
                                    'runner': runner,
                                    'speed_rating': speed_rating,
                                    'units': units,
                                    'market_rank': market_rank,
                                    'confidence': confidence,
                                })

                        if bet_candidates:
                            bet_candidates.sort(key=lambda x: (-x['speed_rating'], x['market_rank']))
                            best_bet = bet_candidates[0]
                            runner   = best_bet['runner']
                            sr       = best_bet['speed_rating']
                            units    = best_bet['units']
                            mkt_rank = best_bet['market_rank']
                            conf_pct = int(best_bet['confidence'] * 100)

                            bet_tracker.record_bet(
                                track=race.track_name, race_num=race.race_number,
                                horse_name=runner.name, horse_num=runner.saddlecloth,
                                price=runner.price, units=units, rsi=sr,
                                race_time=race.start_time,
                                market_rank=mkt_rank, bet_type="NEX BET"
                            )
                            pf_lbl = f"{runner.pf_score or sr:.0f}"
                            tip_kwargs = dict(
                                race_time=race_time_str, track=race.track_name,
                                race_num=race.race_number, distance=race.distance,
                                surface=race.surface, horse_num=runner.saddlecloth,
                                horse_name=runner.name, price=runner.price,
                                units=units, rsi=pf_lbl,
                                market_rank=mkt_rank, bet_type="NEX BET"
                            )
                            if discord:
                                discord.send_tip(**tip_kwargs)
                            if discord2:
                                discord2.send_tip(**tip_kwargs)
                            print(f"\n⏰ {race_time_str} | {race.track_name} R{race.race_number} [💠 NEX BET]")
                            print(f"   {runner.saddlecloth}. {runner.name} @ ${runner.price:.2f}")
                            print(f"   {units:.2f}u | Conf {conf_pct}% | PF Score {pf_lbl} | WinPct {runner.win_pct:.0f}% | Rank {mkt_rank}")

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
    