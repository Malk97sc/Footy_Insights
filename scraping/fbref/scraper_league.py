import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd
from io import StringIO

FBREF_BASE_URL = "https://fbref.com"

def build_fixture_url(competition_id, season_slug, league_name):
    """
    ejm: (9, "2023-2024", "Premier-League") = Premier League 2023-24 fixtures.

    general form:
    https://fbref.com/en/comps/{competition_id}/{season_slug}/schedule/{season_slug}-{league_name}-Scores-and-Fixtures
    """
    return f"{FBREF_BASE_URL}/en/comps/{competition_id}/{season_slug}/schedule/{season_slug}-{league_name}-Scores-and-Fixtures"

def extract_commented_table(soup):
    """
    extract the first table found 
    """
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        if "table" in comment and "Scores and Fixtures" in comment:
            comment_soup = BeautifulSoup(comment, "html.parser")
            table = comment_soup.find("table")
            if table:
                return table
    return None

def scrape_fixtures(competition_id = 9, season_slug= "2023-2024", league_name = "Premier-League"):
    """
    scrape fixtures
    """
    url = build_fixture_url(competition_id, season_slug, league_name)
    print(f"Fetching data from: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find("table")
    if not table:
        table = extract_commented_table(soup)

    if table is None:
        print("Fixtures table not found.")
        return None

    df = pd.read_html(StringIO(str(table)))[0] #we need to read the html table of fbref
    df = df.dropna(subset=["Date"]).reset_index(drop=True)

    match_urls = []
    for row in table.find_all("tr"): #only the rows with match_report
        cell = row.find("td", {"data-stat": "match_report"})
        if cell and cell.find("a"):
            href = cell.find("a")["href"]
            full_url = FBREF_BASE_URL + href
            match_urls.append(full_url)

    if len(df) != len(match_urls):
        print(f"Warning: the len of the datagrame ({len(df)}) and the links ({len(match_urls)}) not match.")
        min_len = min(len(df), len(match_urls))
        df = df.iloc[:min_len]
        match_urls = match_urls[:min_len]

    df["Match URL"] = match_urls #the most important column

    return df

def combine_all_stats(self, season="2023-2024"):
    stats_path = self.data_dir / "team_stats" / "long" / season
    all_files = list(stats_path.glob("*.csv"))
    all_dfs = [pd.read_csv(f) for f in all_files]
    df_combined = pd.concat(all_dfs, ignore_index=True)
    df_combined.to_csv(self.data_dir / f"team_stats_long_{season}.csv", index=False)
