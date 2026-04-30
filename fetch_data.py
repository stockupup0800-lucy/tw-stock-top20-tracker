import requests
import json
import os
from datetime import datetime, date
import time

DATA_FILE = "data.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/javascript, */*",
    "Referer": "https://www.twse.com.tw/"
}

def get_today_str():
    return date.today().strftime("%Y%m%d")

def is_weekday():
    return date.today().weekday() < 5

def fetch_twse(date_str, retries=3, wait=600):
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX20?response=json&date={date_str}&_={int(time.time()*1000)}"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            data = r.json()
            if data.get("stat") == "OK" and data.get("data"):
                stocks = []
                for i, row
