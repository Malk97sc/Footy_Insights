import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scraper import get_all_season_games


df = get_all_season_games(league='Premier League', save_data=True)
print(df.head())


