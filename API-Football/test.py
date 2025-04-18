from scripts.api_fetcher import get_leagues

leagues = get_leagues()
for l in leagues["response"]:
    if (l["league"]["name"] == "Premier League" 
        and l["country"]["name"] == "England"):
        print("English Premier League finded:")
        print(f"ID: {l['league']['id']}")
        print(f"Years available: {[s['year'] for s in l['seasons']]}")
        break
