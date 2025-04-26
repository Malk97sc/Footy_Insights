import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scraper import get_league_top_players_stats, get_today_games

df = get_league_top_players_stats(league='Premier League')
df = get_today_games('Premier League')
print(df.head())