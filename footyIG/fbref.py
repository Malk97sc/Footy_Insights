import requests
from bs4 import BeautifulSoup, Comment
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from io import StringIO
import pandas as pd
import time
from pathlib import Path

class Fbref:
    BASE_URL = "https://fbref.com"

    def __init__(self, data_dir="data/raw/fbref"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def build_fixture_url(self, competition_id, season_slug, league_name):
        return f"{self.BASE_URL}/en/comps/{competition_id}/{season_slug}/schedule/{season_slug}-{league_name}-Scores-and-Fixtures"

    def extract_commented_table(self, soup):
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if "table" in comment and "Scores and Fixtures" in comment:
                return BeautifulSoup(comment, "html.parser").find("table")
        return None

    def scrape_fixtures(self, competition_id=9, season_slug="2023-2024", league_name="Premier-League"):
        url = self.build_fixture_url(competition_id, season_slug, league_name)
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table") or self.extract_commented_table(soup)
        if not table:
            return None
        df = pd.read_html(StringIO(str(table)))[0].dropna(subset=["Date"]).reset_index(drop=True)

        urls = [
            self.BASE_URL + cell.find("a")["href"]
            for row in table.find_all("tr")
            if (cell := row.find("td", {"data-stat": "match_report"})) and cell.find("a")
        ]
        if len(df) != len(urls):
            df = df.iloc[:len(urls)]
        df["Match URL"] = urls
        return df

    def extract_match_id(self, url):
        return urlparse(url).path.split('/')[3]

    def scrape_team_stats(self, url, headless=True):
        options = Options()
        if headless:
            options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(5)

        team_html = driver.find_element(By.ID, "team_stats").get_attribute("outerHTML")
        extra_html = driver.find_element(By.ID, "team_stats_extra").get_attribute("outerHTML")
        driver.quit()

        main_rows, home, away = self.parse_team_stats_html(team_html)
        extra_rows = self.parse_team_stats_extra_html(extra_html, home, away)

        df_main = pd.DataFrame(main_rows, columns=["Stat", home, away])
        df_extra = pd.DataFrame(extra_rows, columns=["Stat", home, away])
        return df_main, df_extra, home, away

    def parse_team_stats_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        rows = table.find_all("tr")
        home = rows[0].find("th", style="text-align: right;").get_text(strip=True)
        away = rows[0].find("th", style="text-align: left;").get_text(strip=True)
        data = []
        for i in range(1, len(rows), 2):
            th = rows[i].find("th")
            if not th: continue
            stat = th.get_text(strip=True)
            tds = rows[i+1].find_all("td")
            data.append([stat, tds[0].get_text(" ", strip=True), tds[1].get_text(" ", strip=True)])
        return data, home, away

    def parse_team_stats_extra_html(self, html, home, away):
        soup = BeautifulSoup(html, "html.parser")
        container = soup.find(id="team_stats_extra")
        data = []
        if container:
            for block in container.find_all("div", recursive=False):
                values = [d.get_text(strip=True) for d in block.find_all("div", recursive=False) if "th" not in (d.get("class") or [])]
                for i in range(0, len(values), 3):
                    if i + 2 < len(values):
                        data.append({"Stat": values[i+1], home: values[i], away: values[i+2]})
        return data

    def melt_team_stats(self, df, tag):
        return df.melt(id_vars=["Stat"], var_name="Team", value_name="Value").assign(Table=tag)

    def scrape_and_save_match_stats(self, url, headless=True):
        match_id = self.extract_match_id(url)
        df_main, df_extra, home, away = self.scrape_team_stats(url, headless)
        df_main_long = self.melt_team_stats(df_main, "Main")
        df_extra_long = self.melt_team_stats(df_extra, "Extra")
        df_combined = pd.concat([df_main_long, df_extra_long], ignore_index=True)
        df_combined["MatchID"] = match_id

        out_path = self.data_dir / "team_stats" / "long"
        out_path.mkdir(parents=True, exist_ok=True)
        df_combined.to_csv(out_path / f"{match_id}.csv", index=False)
        return df_combined
    
    def combine_all_stats(self, season="2023-2024"):
        stats_path = self.data_dir / "team_stats" / "long" / season
        all_files = list(stats_path.glob("*.csv"))
        all_dfs = [pd.read_csv(f) for f in all_files]
        df_combined = pd.concat(all_dfs, ignore_index=True)
        df_combined.to_csv(self.data_dir / f"team_stats_long_{season}.csv", index=False)
