import json
from pathlib import Path
from api_fetcher import get_fixtures_by_league_season

LEAGUE_ID = 39  #premier league id
SEASON = 2023 #2024+ not works for free users

fixtures = get_fixtures_by_league_season(LEAGUE_ID, SEASON)

if fixtures:
    out_dir = Path(__file__).resolve().parents[1] / "data" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"fixtures_premier_{SEASON}.json"

    with open(out_path, "w") as f:
        json.dump(fixtures, f, indent=2)

    print(f"Save in: {out_path}")