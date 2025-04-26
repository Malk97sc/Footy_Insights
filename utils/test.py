from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
from bs4 import BeautifulSoup
import time

def parse_team_stats_html(team_stats_html):
    """
    returns (data, home_team, away_team) where data is a list of [stat, home_val, away_val].
    """
    soup = BeautifulSoup(team_stats_html, "html.parser")
    table = soup.find("table")
    rows = table.find_all("tr")

    #extract the name of the teams
    header_row = rows[0]
    home_th = header_row.find("th", style="text-align: right;")
    home_team = home_th.get_text(strip=True) if home_th else "Home"
    away_th = header_row.find("th", style="text-align: left;")
    away_team = away_th.get_text(strip=True) if away_th else "Away"

    data = []
    for i in range(1, len(rows), 2):
        th = rows[i].find("th")
        if not th:
            continue
        stat = th.get_text(strip=True)

        tds = rows[i+1].find_all("td")
        home = tds[0].get_text(" ", strip=True)
        away = tds[1].get_text(" ", strip=True)
        data.append([stat, home, away])

    return data, home_team, away_team

def parse_team_stats_extra_html(extra_html, home_team, away_team):
    """
    returns a list of dictionaries with:
    { "stat": <stat name>, 
        <home_team>: <home value>, 
        <away_team>: <away value> }
    """
    soup = BeautifulSoup(extra_html, "html.parser")
    container = soup.find(id="team_stats_extra")
    if not container:
        return []

    data = []
    for block in container.find_all("div", recursive=False):
        valores = [
            d.get_text(strip=True)
            for d in block.find_all("div", recursive=False)
            if "th" not in (d.get("class") or [])
        ]
        for i in range(0, len(valores), 3):
            if i+2 < len(valores):
                home_val, stat, away_val = valores[i], valores[i+1], valores[i+2]
                #print(home_val)
                #print(stat)
                #print(away_val)
                data.append({
                    "Stat": stat,
                    home_team: home_val,
                    away_team: away_val
                })

    return data


def scrape_team_stats(url: str, headless: bool = True):
    options = Options()
    if headless:
        options.add_argument("--headless")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)

    team_stats_html = driver.find_element(By.ID, "team_stats").get_attribute("outerHTML")
    team_stats_extra_html = driver.find_element(By.ID, "team_stats_extra").get_attribute("outerHTML")
    driver.quit()

    #to see the content of the 
    #print(team_stats_html)
    #print(team_stats_extra_html)

    #parse team_stats to get team names and key data
    main_rows, home, away = parse_team_stats_html(team_stats_html)
    extra_rows = parse_team_stats_extra_html(team_stats_extra_html, home, away)

    df_main = pd.DataFrame(main_rows, columns=["Stat", home, away])
    df_extra = pd.DataFrame(extra_rows, columns=["Stat", home, away])

    return df_main, df_extra

if __name__ == "__main__":
    url = "https://fbref.com/en/matches/3a6836b4/Burnley-Manchester-City-August-11-2023-Premier-League"
    df_main, df_extra = scrape_team_stats(url, headless=False)

    print("\nTeam Stats Table:")
    print(df_main)

    print("\nTeam Stats Extra:")
    print(df_extra)

    df_main.to_csv('df_main.csv', index=False)
    df_extra.to_csv('df_extra.csv', index=False)
