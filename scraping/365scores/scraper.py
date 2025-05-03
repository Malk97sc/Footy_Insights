import pandas as pd
import time
import json
import requests 
import sys
import re
from pathlib import Path
from datetime import datetime
from dateutil import parser as date_parser  

sys.path.append(str(Path(__file__).resolve().parents[2]))
from footyIG.config import *

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

def validate_league(league, page='365Scores'):
    possible_leagues = get_possible_leagues_for_page(page)
    if league not in possible_leagues:
        raise ValueError(f"League '{league}' is not available. Choose one of: {list(possible_leagues.keys())}")
    return possible_leagues[league]

def get_all_season_games(league, save_data = False, save_json = False):
    """
    Get ALL season games (historical) for a given league.

    Args:
        league (str): Name of the league (must exist in get_possible_leagues_for_page()).
        save_data (bool): Save all the games in csv file if True.
        save_json (bool):  Save raw JSON if True.

    Returns:
        pd.DataFrame: All season games.
    """
    league_config = validate_league(league, page='365Scores')
    league_id = league_config['id']
    url_name = league_config['URLname']

    base_url   = "https://webws.365scores.com"
    results_ep = f"{base_url}/web/games/results/"
    base_params     = {
        'appTypeId': 5,
        'langId': 29,
        'timezoneName': 'America/Bogota',
        'userCountryId': 109,
        'competitions': league_id,
        'showOdds': 'true',
        'includeTopBettingOpportunity': 1,
        'topBookmaker': 4
    }

    resp0 = requests.get(results_ep, params=base_params)
    resp0.raise_for_status()
    data0      = resp0.json()
    snapshot   = data0['lastUpdateId']
    round_keys = [
        rf['key'] for rf in data0.get('roundFilters', [])
        if rf['key'] #skip the "" in all games
    ]

    all_games = []

    for rk in round_keys: 
        params = {
            **base_params,
            'lastUpdateId': snapshot,
            'roundKey':     rk
        }
        r = requests.get(results_ep, params=params)
        r.raise_for_status()
        games = r.json().get('games', [])
        all_games.extend(games)

        if save_json:
            with open(f'{url_name}_raw_matches.json','w',encoding='utf-8') as f:
                json.dump(all_games, f, ensure_ascii=False, indent=4)

        time.sleep(0.5)  #wait the server connection

    records = []
    for g in all_games:
        h = g['homeCompetitor']
        a = g['awayCompetitor']
        dt = date_parser.parse(g['startTime'])
        records.append({
            'roundNum': g.get('roundNum'),
            'roundName': g.get('roundName'),
            'match_date': dt.strftime("%Y-%m-%d"),
            'start_time': dt.strftime("%H:%M"),
            'home_team': h['name'],
            'away_team': a['name'],
            'home_id': h['id'],
            'away_id': a['id'],
            'league_id': league_id,
            'match_id': g['id'],
            'match_url': (
                f"https://www.365scores.com/es/football/match/"
                f"{url_name}-{league_id}/" 
                f"{h['nameForURL']}-{a['nameForURL']}-"
                f"{h['id']}-{a['id']}-{league_id}"
                f"#id={g['id']}"
            ),
            '_dt': dt  #to sort
        })

    df = pd.DataFrame.from_records(records)
    df['roundNum'] = pd.to_numeric(df['roundNum'], errors='coerce') #to sort the dataFrame
    df = df.sort_values(['roundNum', '_dt']).reset_index(drop=True).drop(columns=['_dt'])
    
    if save_data:
        df.to_csv(f'{url_name}_matches.csv', index=False)

    return df

def get_today_games(league, save_data = False):
        """
            Get all today games for a league

            Args:
            league (str): Possible leagues in get_available_leagues("365Scores").
                          The page don't show stats from previous seasons.

            Returns:
                df: DataFrame with all the games.
        """

        league_config = validate_league(league, page='365Scores')
        league_id = league_config['id']
        url_name = league_config['URLname']

        url = f'https://webws.365scores.com/web/games/?appTypeId=5&langId=29&competitions={league_id}'

        response = requests.get(url, headers)
        if response.status_code != 200:
            raise Exception(f"Error in competitions request: {response.status_code}")
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

                match_url = f"https://www.365scores.com/es/football/match/{url_name}-{league_id}/{home_for_url}-{away_for_url}-{home_id}-{away_id}-{league_id}#id={match_id}"

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
        league_config = validate_league(league, page='365Scores')
        league_id = league_config['id']
        url_name = league_config['URLname']
        
        url = f'https://webws.365scores.com/web/stats/?appTypeId=5&langId=29&timezoneName=America/Bogota&userCountryId=170&competitions={league_id}&competitors=&withSeasons=true'
        response = requests.get(url, headers=headers)
        time.sleep(2)
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

def get_players(match_url, save_data = False):
    """Get players info for a certain match

    Args:
        match_url (url): 365Scores match URL

    Returns:
        teams_df: Player data for a match as a DataFrame.
    """
    match_dt = get_match_data(match_url)
    teams = match_dt['members']
    team_df = pd.DataFrame(teams)
    matchup_id, game_id = get_ids(match_url)
    if save_data:
        team_df.to_csv(f'players_data_{game_id}.csv', index=False)
    return team_df

def get_players_stats(match_url, save_data=False, save_json=False):
    """
    Extract all general statistics for all players in a match.

    Args:
        match_url (str): Match URL from 365Scores.
        save_data (bool): Save the data to a CSV file.

    Returns:
        pd.DataFrame: Player statistics for the match.
    """
    match_data = get_match_data(match_url)
    matchup_id, game_id = get_ids(match_url)

    if not match_data.get('hasLineups'):
        print(f"[INFO] Match {game_id} has no lineups. Skipping individual stats.")
        return pd.DataFrame()

    #Search all players info to map names and positions
    players_info_df = get_players(match_url, save_data=False)
    id_to_name = dict(zip(players_info_df['id'], players_info_df['name']))
    id_to_position = {
        row['id']: row.get('position', {}).get('name') for _, row in players_info_df.iterrows()
    }

    rows = []
    for side in ['homeCompetitor', 'awayCompetitor']:
        team = match_data.get(side, {})
        team_name = team.get('name', 'Unknown')
        players = team.get('lineups', {}).get('members', [])

        for p in players:
            player_id = p.get('id')
            player_name = id_to_name.get(player_id, 'Unknown')
            position = id_to_position.get(player_id, None)
            stats = p.get('stats', [])

            for stat in stats:
                stat_name = stat.get('name')
                value = stat.get('value')
                rows.append({
                    'match_id': game_id,
                    'team': team_name,
                    'player_id': player_id,
                    'player_name': player_name,
                    'position': position,
                    'stat_name': stat_name,
                    'value': value
                })

    df = pd.DataFrame(rows)

    if save_data:
        df.to_csv(f'full_individual_stats_{game_id}.csv', index=False)

    return df



