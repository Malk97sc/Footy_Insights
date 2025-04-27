import pandas as pd
import time
import json
import requests 
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parents[2]))
from footyIG.config import *

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

def get_today_games(league, debug = False):
        """
            Get all today games for a league

            Args:
            league (str): Possible leagues in get_available_leagues("365Scores").
                          The page don't show stats from previous seasons.

            Returns:
                df: DataFrame with all the games.
        """

        leagues = get_possible_leagues_for_page('365Scores')
        #print(leagues)
        league_id = leagues[league]['id']

        url = f'https://webws.365scores.com/web/games/?appTypeId=5&langId=29&competitions={league_id}'

        response = requests.get(url, headers)
        data = response.json()

        if debug:
            with open(f'today_games{league}.json', 'w') as json_file:
                json.dump(data, json_file, indent=4)

        #print(data)
        games = data['games']   
        today = datetime.now().date()
        match_list = []

        for game in games:
            game_datetime = datetime.fromisoformat(game['startTime'].replace('Z', '+00:00'))
            game_date = game_datetime.date()

            if game_date == today:
                home = game['homeCompetitor']
                away = game['awayCompetitor']

                home_name = home['name']
                away_name = away['name']

                home_for_url = home['nameForURL']
                away_for_url = away['nameForURL']
                home_id = home['id']
                away_id = away['id']
                match_id = game['id']

                match_url = f"https://www.365scores.com/es/football/match/premier-league-{league_id}/{home_for_url}-{away_for_url}-{home_id}-{away_id}-{league_id}#id={match_id}"

                match_list.append({
                    'home_team': home_name,
                    'away_team': away_name,
                    'start_time': game_datetime.strftime("%H:%M"),
                    'match_url': match_url
                })

        df = pd.DataFrame(match_list)
        return df

def parse_dataframe(objeto):
        df = pd.DataFrame(objeto['rows'])
        df_1 = df['entity'].apply(pd.Series)
        df_2 = df['stats'].apply(pd.Series)[0].apply(pd.Series)
        df_concat = pd.concat([df_1, df_2], axis=1)[['id', 'name', 'positionName', 'value']]
        df_concat['estadistica'] = objeto['name']
        return df_concat

def get_league_top_players_stats(league, debug = False):
        """Get top performers of certain statistics for a league and a season

        Args:
            league (str): Possible leagues in get_available_leagues("365Scores").
                          The page don't show stats from previous seasons.

        Returns:
            df: DataFrame with all the stats, values and players.
        """
        leagues = get_possible_leagues_for_page('365Scores')
        #print(leagues)
        league_id = leagues[league]['id']
        #print(league_id)
        
        response = requests.get(f'https://webws.365scores.com/web/stats/?appTypeId=5&langId=29&timezoneName=America/Bogota&userCountryId=170&competitions={league_id}&competitors=&withSeasons=true', headers=headers)
        
        time.sleep(3)
        stats = response.json()
        #print(stats)
        general_stats = stats['stats']

        if debug:
            with open(f'general_stats_{league}.json', 'w') as json_file:
                json.dump(general_stats, json_file, indent=4)
        
        athlete = general_stats['athletesStats']
        #print(athlete)

        df = pd.DataFrame()        
        for i in range(len(athlete)):
            obj = athlete[i]
            stats_df = parse_dataframe(obj)
            df = pd.concat([df, stats_df])
        return df
