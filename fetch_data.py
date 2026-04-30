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
                for i, row in enumerate(data["data"][:20]):
                   # 新的（正確欄位）
change_sign = str(row[9]).strip() if len(row) > 9 else ""
change_val = str(row[10]).strip() if len(row) > 10 else "--"
# 漲跌符號可能含 HTML tag，清理一下
if "+" in change_sign or "green" in change_sign.lower():
    change_display = f"+{change_val}"
elif "-" in change_sign or "red" in change_sign.lower():
    change_display = f"-{change_val}"
else:
    change_display = change_val

stocks.append({
    "rank": i + 1,
    "code": str(row[0]).strip(),
    "name": str(row[1]).strip(),
    "price": str(row[8]).strip() if len(row) > 8 else "--",
    "change": change_display,
    "turnover": str(row[4]).strip(),
})
                return stocks, data.get("date", date_str)
            else:
                print(f"第 {attempt+1} 次嘗試：上市資料尚未更新，{wait//60} 分鐘後重試...")
                if attempt < retries - 1:
                    time.sleep(wait)
        except Exception as e:
            print(f"第 {attempt+1} 次嘗試失敗：{e}")
            if attempt < retries - 1:
                time.sleep(wait)
    return None, None

def fetch_tpex(date_str, retries=3, wait=600):
    y = int(date_str[:4]) - 1911
    m = date_str[4:6]
    d = date_str[6:8]
    # 改用 date 參數格式
    url = f"https://www.tpex.org.tw/web/stock/aftertrading/top20_turnover/turnover_result.php?l=zh-tw&o=json&d={y}/{m}/{d}&_={int(time.time()*1000)}"
    for attempt in range(retries):
        try:
            headers = {**HEADERS, "Referer": "https://www.tpex.org.tw/"}
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            text = r.text.strip()
            if not text:
                raise ValueError("空回應")
            data = json.loads(text)
            if data.get("aaData"):
                stocks = []
                for i, row in enumerate(data["aaData"][:20]):
                    stocks.append({
                        "rank": i + 1,
                        "code": str(row[0]).strip(),
                        "name": str(row[1]).strip(),
                        "price": str(row[2]).strip() if len(row) > 2 else "--",
                        "change": str(row[3]).strip() if len(row) > 3 else "--",
                        "turnover": str(row[4]).strip() if len(row) > 4 else "--",
                    })
                return stocks, date_str
            else:
                print(f"第 {attempt+1} 次嘗試：上櫃資料尚未更新，{wait//60} 分鐘後重試...")
                if attempt < retries - 1:
                    time.sleep(wait)
        except Exception as e:
            print(f"第 {attempt+1} 次嘗試失敗：{e}")
            if attempt < retries - 1:
                time.sleep(wait)
    return None, None

def fetch_tpex(date_str, retries=3, wait=600):
    y = int(date_str[:4]) - 1911
    m = date_str[4:6]
    d = date_str[6:8]
    url = f"https://www.tpex.org.tw/web/stock/aftertrading/top20_turnover/turnover_result.php?l=zh-tw&o=json&d={y}/{m}/{d}&_={int(time.time()*1000)}"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers={**HEADERS, "Referer": "https://www.tpex.org.tw/"}, timeout=30)
            r.raise_for_status()
            data = r.json()
            if data.get("aaData"):
                stocks = []
                for i, row in enumerate(data["aaData"][:20]):
                    stocks.append({
                        "rank": i + 1,
                        "code": row[0].strip(),
                        "name": row[1].strip(),
                        "price": row[2].strip() if len(row) > 2 else "--",
                        "change": row[3].strip() if len(row) > 3 else "--",
                        "turnover": row[4].strip() if len(row) > 4 else "--",
                    })
                return stocks, date_str
            else:
                print(f"第 {attempt+1} 次嘗試：上櫃資料尚未更新，{wait//60} 分鐘後重試...")
                if attempt < retries - 1:
                    time.sleep(wait)
        except Exception as e:
            print(f"第 {attempt+1} 次嘗試失敗：{e}")
            if attempt < retries - 1:
                time.sleep(wait)
    return None, None

def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"history": {}, "last_updated": ""}

def compute_streaks(history, date_str, stocks):
    all_dates = sorted(history.keys())
    if date_str not in all_dates:
        all_dates.append(date_str)
    all_dates = sorted(all_dates)
    today_codes = {s["code"] for s in stocks}
    streaks = {}
    for code in today_codes:
        count = 0
        for d in reversed(all_dates):
            day_codes = set(history.get(d, {}).get("codes", []))
            if d == date_str:
                day_codes = today_codes
            if code in day_codes:
                count += 1
            else:
                break
        streaks[code] = count
    return streaks

def main():
    if not is_weekday():
        print("今日為假日，跳過。")
        return

    today = get_today_str()
    print(f"抓取日期：{today}")
    existing = load_existing()
    history = existing.get("history", {})

    twse_stocks, twse_date = fetch_twse(today)
    if twse_stocks:
        print(f"上市：取得 {len(twse_stocks)} 筆，日期 {twse_date}")
        if twse_date not in history:
            history[twse_date] = {}
        history[twse_date]["twse"] = {"codes": [s["code"] for s in twse_stocks], "stocks": twse_stocks}
        twse_streaks = compute_streaks(
            {d: {"codes": v.get("twse", {}).get("codes", [])} for d, v in history.items()},
            twse_date, twse_stocks
        )
        for s in twse_stocks:
            s["streak"] = twse_streaks.get(s["code"], 1)
    else:
        print("上市：3 次都失敗，今日無資料")

    tpex_stocks, tpex_date = fetch_tpex(today)
    if tpex_stocks:
        print(f"上櫃：取得 {len(tpex_stocks)} 筆")
        if today not in history:
            history[today] = {}
        history[today]["tpex"] = {"codes": [s["code"] for s in tpex_stocks], "stocks": tpex_stocks}
        tpex_streaks = compute_streaks(
            {d: {"codes": v.get("tpex", {}).get("codes", [])} for d, v in history.items()},
            today, tpex_stocks
        )
        for s in tpex_stocks:
            s["streak"] = tpex_streaks.get(s["code"], 1)
    else:
        print("上櫃：3 次都失敗，今日無資料")

    all_dates = sorted(history.keys())
    if len(all_dates) > 365:
        for old in all_dates[:-365]:
            del history[old]

    output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "today": today,
        "twse": twse_stocks or [],
        "tpex": tpex_stocks or [],
        "history": history
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"✅ 完成，歷史共 {len(history)} 天")

if __name__ == "__main__":
    main()
