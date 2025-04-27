import pandas as pd
import time
import json
import requests 
import sys
import re
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parents[2]))
from footyIG.config import *

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

def get_today_games(league, save_data = False):
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

        if save_data:
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
                    'match_url': match_url,
                    'home_id': home_id,
                    'away_id': away_id,
                    'league_id': league_id,
                    'match_id': match_id
                })

        df = pd.DataFrame(match_list)
        return df

def parse_dataframe(obj):
        df = pd.DataFrame(obj['rows'])
        df_1 = df['entity'].apply(pd.Series)
        df_2 = df['stats'].apply(pd.Series)[0].apply(pd.Series)
        df_concat = pd.concat([df_1, df_2], axis=1)[['id', 'name', 'positionName', 'value']]
        df_concat['estadistica'] = obj['name']
        return df_concat

def get_league_top_players_stats(league, save_data = False):
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

        if save_data:
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

def get_ids(match_url):
    """Extracts matchup_id and game_id from match URL."""
    matchup_match = re.search(r'-(\d+-\d+-\d+)', match_url)
    matchup_id = matchup_match.group(1) if matchup_match else None

    game_match = re.search(r'id=(\d+)', match_url)
    game_id = game_match.group(1) if game_match else None

    return matchup_id, game_id

def get_match_data(match_url, save_data = False):
    """Fetch complete match data from 365Scores.
        Args:
            match_url: Link of the game
            save_data: To save the json data. Default is False
        
        Returns:
            match_data: Json with all the stats from a match"""
    matchup_id, game_id = get_ids(match_url)
    if not matchup_id or not game_id:
        raise ValueError("Fail to extract matchup_id or game_id.")

    url = f'https://webws.365scores.com/web/game/?appTypeId=5&langId=29&timezoneName=America/Buenos_Aires&userCountryId=382&gameId={game_id}&matchupId={matchup_id}&topBookmaker=14'

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error in request: {response.status_code}")
    
    time.sleep(2)

    data = response.json()
    #print(data)

    match_data = data['game']

    if save_data:
        with open(f'match_stats_{game_id}.json', 'w') as json_file:
            json.dump(match_data, json_file, indent=4)

    return match_data

def get_match_stats(game_id):
    """Fetch statistics for a match from 365Scores."""
    url = f'https://webws.365scores.com/web/game/stats/?appTypeId=5&langId=29&timezoneName=America/Buenos_Aires&userCountryId=382&games={game_id}'
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error in stats request: {response.status_code}")

    time.sleep(2)

    data = response.json()
    return data

def extract_statistics(match_url):
    """
    Extract and organize match statistics into a DataFrame.

    Args:
        match_url (str): URL of the match on 365Scores.

    Returns:
        df_stats (DataFrame): Organized DataFrame with real team names.
    """

    matchup_id, game_id = get_ids(match_url)
    match_data = get_match_data(match_url)

    try:
        status_group = match_data['statusGroup']
    except KeyError:
        print("Error: 'statusGroup' not found in match_data.")
        return pd.DataFrame()

    stats_dict = {}

    if status_group in [3, 4]:  # Match in progress or ended
        stats_data = get_match_stats(game_id)

        try:
            statistics = stats_data['statistics']
            competitors = stats_data['competitors']

            team1_id = competitors[0]['id']
            team1_name = competitors[0]['name']

            team2_id = competitors[1]['id']
            team2_name = competitors[1]['name']

            for stat in statistics:
                stat_name = stat.get('name', 'Unknown')
                team_id = stat.get('competitorId')
                value = stat.get('value')

                if stat_name not in stats_dict:
                    stats_dict[stat_name] = {}

                if team_id == team1_id:
                    stats_dict[stat_name][team1_name] = value
                elif team_id == team2_id:
                    stats_dict[stat_name][team2_name] = value

        except KeyError:
            print("Error: Unexpected statistics format in stats_data.")
            return pd.DataFrame()

    elif status_group == 2:  # Match not started (scheduled)
        try:
            home_stats = match_data['homeCompetitor']['seasonStatistics']
            away_stats = match_data['awayCompetitor']['seasonStatistics']

            home_team_name = match_data['homeCompetitor']['name']
            away_team_name = match_data['awayCompetitor']['name']

            for stat_category in set(home_stats.keys()).union(set(away_stats.keys())):
                home_value = home_stats.get(stat_category, None)
                away_value = away_stats.get(stat_category, None)

                stats_dict[stat_category] = {
                    home_team_name: home_value,
                    away_team_name: away_value
                }
        except KeyError:
            print("Error: 'seasonStatistics' not found for one of the teams.")
            return pd.DataFrame()

    else:
        print(f"Info: Match with unknown statusGroup = {status_group}. No statistics extracted.")
        return pd.DataFrame()

    if not stats_dict:
        print("Warning: No statistics extracted after processing.")
        return pd.DataFrame()

    df_stats = pd.DataFrame.from_dict(stats_dict, orient='index')
    df_stats.index.name = 'Statistic'
    df_stats.reset_index(inplace=True)

    return df_stats
