import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scraper import get_match_data, extract_statistics

match_url = "https://www.365scores.com/es-mx/football/match/premier-league-7/bournemouth-manchester-united-50-105-7#id=4147350"

#match_data = get_match_data(match_url)
#print(match_data)
statistics = extract_statistics(match_url)
print(statistics.head())