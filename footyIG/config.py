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
            'Bundesliga': {'id': 25, 'seasons': None},
            'DFB-Pokal': {'id': 28, 'seasons': None},
            'Premier League': {'id': 7, 'seasons': None},
            'FA Cup': {'id': 8, 'seasons': None},
            'LaLiga': {'id': 11, 'seasons': None},
            'Copa del Rey': {'id': 13, 'seasons': None},
            'Brasileirao': {'id': 113, 'seasons': None},
            'Primera Division Colombia': {'id': 620, 'seasons': None},
            'Champions League': {'id': 572, 'seasons': None},
            'Copa America': {'id': 595, 'seasons': None},
            'Euros': {'id': 6316, 'seasons': None},
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

def get_possible_leagues_for_page(page):
    """Get possible leagues for a particular page."""
    leagues = get_possible_leagues('Bundesliga', '2023', page)[page] #bundes is just arbitrary value
    return leagues

def get_available_pages():
    """Get available scraping pages."""
    return ['365Scores']
