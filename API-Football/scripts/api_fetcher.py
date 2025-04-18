import requests
import json
from pathlib import Path

def load_api():
    config_path = Path(__file__).resolve().parents[1] / "config" / "api_keys.json"
    with open(config_path) as f:
        return json.load(f)["api_football_key"]
    
API_KEY = load_api()
BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

def get(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def get_leagues():
    return get("leagues")


def get_fixtures_by_league_season(league_id, season):
    """
    download all the matches of a league in a season
    """
    fixtures = get("fixtures", {
        "league": league_id,
        "season": season
    })

    if fixtures:
        print(f"Matches obtained: {len(fixtures['response'])}")
    return fixtures
