import requests
import pandas as pd
from bs4 import BeautifulSoup, Comment
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from pathlib import Path
from io import StringIO

class FBrefScraper:
    BASE_URL = "https://fbref.com"

    def build_fixture_url(self, competition_id, season_slug, league_name):
        return f"{self.BASE_URL}/en/comps/{competition_id}/{season_slug}/schedule/{season_slug}-{league_name}-Scores-and-Fixtures"

    def extract_commented_table(self, soup):
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if "table" in comment and "Scores and Fixtures" in comment:
                comment_soup = BeautifulSoup(comment, "html.parser")
                return comment_soup.find("table")
        return None

    def scrape_fixtures(self, competition_id=9, season_slug="2023-2024", league_name="Premier-League"):
        url = self.build_fixture_url(competition_id, season_slug, league_name)
        print(f"Fetching data from: {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        table = soup.find("table") or self.extract_commented_table(soup)
        if not table:
            print("Fixtures table not found.")
            return None

        df = pd.read_html(StringIO(str(table)))[0].dropna(subset=["Date"]).reset_index(drop=True)
        match_urls = [
            self.BASE_URL + a["href"]
            for row in table.find_all("tr")
            if (cell := row.find("td", {"data-stat": "match_report"})) and (a := cell.find("a"))
        ]

        min_len = min(len(df), len(match_urls))
        df = df.iloc[:min_len]
        df["Match URL"] = match_urls[:min_len]

        return df

    def extract_match_id(self, url):
        return urlparse(url).path.split('/')[3]

    def parse_team_stats_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        rows = table.find_all("tr")
        home = rows[0].find("th", style="text-align: right;").get_text(strip=True)
        away = rows[0].find("th", style="text-align: left;").get_text(strip=True)
        data = []
        for i in range(1, len(rows), 2):
            th = rows[i].find("th")
            if th:
                stat = th.get_text(strip=True)
                tds = rows[i+1].find_all("td")
                data.append([stat, tds[0].get_text(" ", strip=True), tds[1].get_text(" ", strip=True)])
        return data, home, away

    def parse_team_stats_extra_html(self, html, home, away):
        soup = BeautifulSoup(html, "html.parser")
        container = soup.find(id="team_stats_extra")
        if not container:
            return []

        data = []
        for block in container.find_all("div", recursive=False):
            values = [d.get_text(strip=True) for d in block.find_all("div", recursive=False) if "th" not in (d.get("class") or [])]
            for i in range(0, len(values), 3):
                if i + 2 < len(values):
                    data.append({"Stat": values[i+1], home: values[i], away: values[i+2]})
        return data

    def scrape_match_stats(self, url, headless=True):
        options = Options()
        if headless:
            options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(5)

        team_stats_html = driver.find_element(By.ID, "team_stats").get_attribute("outerHTML")
        team_stats_extra_html = driver.find_element(By.ID, "team_stats_extra").get_attribute("outerHTML")
        driver.quit()

        main_rows, home, away = self.parse_team_stats_html(team_stats_html)
        extra_rows = self.parse_team_stats_extra_html(team_stats_extra_html, home, away)

        df_main = pd.DataFrame(main_rows, columns=["Stat", home, away])
        df_extra = pd.DataFrame(extra_rows, columns=["Stat", home, away])

        return df_main, df_extra, home, away

    def melt_and_save_stats(self, df_main, df_extra, match_id, output_dir="data/raw/fbref/team_stats/long"):
        df_main_long = df_main.melt(id_vars=["Stat"], var_name="Team", value_name="Value").assign(Table="Main")
        df_extra_long = df_extra.melt(id_vars=["Stat"], var_name="Team", value_name="Value").assign(Table="Extra")
        df_combined = pd.concat([df_main_long, df_extra_long], ignore_index=True)
        df_combined["MatchID"] = match_id

        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        df_combined.to_csv(path / f"{match_id}.csv", index=False)
        return df_combined
