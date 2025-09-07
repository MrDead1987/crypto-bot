# config.py
from dotenv import load_dotenv
import os

# Wczytuje plik .env
load_dotenv()

# Pobiera zmienne środowiskowe z .env
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
