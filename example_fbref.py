import footyIG as fty
import pandas as pd
from pathlib import Path

fbref = fty.Fbref()

#Step 1
season = "2023-2024"
fixtures_df = fbref.scrape_fixtures(season_slug = "2023-2024", league_name = "Premier-League")
fixtures_out_path = fbref.data_dir / f"fixtures_{season}.csv"
print(fixtures_df)
fixtures_df.to_csv(fixtures_out_path, index=False)
print(f"Fixtures saved to {fixtures_out_path}")

#Step 2
for idx, url in enumerate(fixtures_df["Match URL"]):
    if idx == 10 : break

    print(f"Scraping match {idx + 1}/{len(fixtures_df)}: {url}")
    try:
        fbref.scrape_and_save_match_stats(url)
    except Exception as e:
        print(f"Failed to scrape match: {url}")
        print(f"Error: {e}")

#Step 3
combined_df = fbref.combine_all_stats(season=season)
print("Combined DataFrame:")
print(combined_df.head(10))