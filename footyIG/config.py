import pandas as pd
import numpy as np

from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
from IPython.display import clear_output
from selenium.webdriver.common.by import By

from .exceptions import *

def get_possible_leagues(league, season, page):
    """Dictionary with all the possible pages, leagues and season for the scraper."""

    possible_leagues = {
        '365Scores': {
            'Bundesliga': {'id': 25, 'URLname': 'bundesliga' ,'seasons': None},
            'DFB-Pokal': {'id': 28, 'URLname': 'dfb-pokal' ,'seasons': None},
            'Premier League': {'id': 7, 'URLname': 'premier-league', 'seasons': None},
            'FA Cup': {'id': 8, 'URLname': 'fa-cup' ,'seasons': None},
            'LaLiga': {'id': 11, 'URLname': 'laliga', 'seasons': None},
            'Copa del Rey': {'id': 13, 'URLname': 'copa-del-rey' ,'seasons': None},
            'Betplay Dimayor': {'id': 620, 'URLname': 'liga-betplay', 'seasons': None},
            'Libertadores': {'id': 102, 'URLname': 'libertadores', 'season': None},
            'Sudamericana': {'id': 389, 'URLname': 'conmebol-sudamericana', 'season': None},
            'Europa League': {'id': 573, 'URLname': 'uefa-europa-league', 'seasons': None},
            'Conference League': {'id': 7685, 'URLname': 'uefa-conference-league', season: None},
            'Champions League': {'id': 572, 'URLname': 'uefa-champions-league', 'seasons': None},
            'Copa America': {'id': 595, 'URLname': 'copa-america', 'seasons': None},
            'Eurocopa': {'id': 6316, 'URLname': 'euro', 'seasons': None},
        },
    }

    if not isinstance(page, str):
        raise InvalidStrType(page)
    
    if page not in possible_leagues:
        raise ValueError(f"Page '{page}' not available. Available pages: {list(possible_leagues.keys())}")

    if not isinstance(league, str):
        raise InvalidStrType(league)
    
    if season is not None and not isinstance(season, str):
        raise InvalidStrType(season)
    
    possible_leagues_list = list(possible_leagues[page].keys())
    if league not in possible_leagues_list:
        raise InvalidLeagueException(league, possible_leagues_list)
    
    if possible_leagues[page][league]['seasons'] is not None:
        possible_seasons_list = list(possible_leagues[page][league]['seasons'])
        if season not in possible_seasons_list:
            raise InvalidSeasonException(season, possible_seasons_list)

    return possible_leagues

def get_all_leagues(page = '365Scores'):
    return list(get_possible_leagues_for_page(page).keys())

def get_possible_leagues_for_page(page):
    """Get possible leagues for a particular page."""
    leagues = get_possible_leagues('Bundesliga', '2023', page)[page] #bundes is just arbitrary value
    return leagues

def get_available_pages():
    """Get available scraping pages."""
    return ['365Scores']
