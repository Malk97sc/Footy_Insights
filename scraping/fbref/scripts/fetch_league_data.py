import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from scraper_league import scrape_fixtures

import os

def main():
    season_slug = "2023-2024"
    league_name =  "Premier-League" 
    #competition_id = FALTA IMPLEMENTARLO
    df = scrape_fixtures(competition_id = 9, season_slug = season_slug, league_name = league_name)

    if df is not None:
        output_path = os.path.join(os.path.dirname(__file__), f'../../../data/raw/fbref/{league_name}', f'{league_name}_{season_slug}_data.csv')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Data saved to: {output_path}")
    else:
        print("League not found")

if __name__ == "__main__":
    main()
    