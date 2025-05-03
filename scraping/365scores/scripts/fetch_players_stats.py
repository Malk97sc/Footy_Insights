import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scraper import *

'''df = get_league_top_players_stats(league='Premier League')
df = get_today_games('Premier League')
print(df.head())

url1 = 'https://www.365scores.com/es-mx/football/match/bundesliga-25/bayern-munich-rb-leipzig-331-7171-25#id=4168062'
df2 = get_players(url1, True)
print(df2.head())'''

url = 'https://www.365scores.com/es-mx/football/match/bundesliga-25/bayern-munich-rb-leipzig-331-7171-25#id=4168062'
df = get_players_stats(url, True)
print(df.head())
