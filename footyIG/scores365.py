import re
import time
import threading
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO

from .config import get_possible_leagues_for_page
from .exceptions import MatchDoesntHaveInfo

import pandas as pd
import requests
from bs4 import BeautifulSoup
from PIL import Image

class Scores365:
    pass