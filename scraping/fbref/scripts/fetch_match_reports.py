import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
from scraper_match_data import extract_match_id, scrape_team_stats, melt_team_stats


if __name__ == "__main__":
    url = "https://fbref.com/en/matches/3a6836b4/Burnley-Manchester-City-August-11-2023-Premier-League"
    match_id = extract_match_id(url)

    df_main, df_extra, home, away = scrape_team_stats(url, headless=False)
    df_main_long = melt_team_stats(df_main, "Main")
    df_extra_long = melt_team_stats(df_extra, "Extra")
    df_combined = pd.concat([df_main_long, df_extra_long], ignore_index=True)
    df_combined["MatchID"] = match_id

    out_path = Path("../../data/raw/fbref/team_stats/long")
    out_path.mkdir(parents=True, exist_ok=True)
    df_combined.to_csv(out_path / f"{match_id}.csv", index=False)

    print(df_combined.head(10))