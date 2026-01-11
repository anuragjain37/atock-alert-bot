import os
import pandas as pd
import yfinance as yf
import requests
from ta.trend import MACD
from ta.momentum import RSIIndicator
from datetime import datetime, timedelta

# ========================
# Telegram configuration
# ========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN or CHAT_ID not found")

def send_alert(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

# ========================
# Load symbols
# ========================
symbols_df = pd.read_excel("symbols_stocks.xlsx")
symbols = symbols_df.iloc[:, 0].dropna().tolist()

# ========================
# Cache setup
# ========================
CACHE_DIR = "data_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_price_data(symbol, lookback_days=365):
    safe_symbol = symbol.replace("-", "_")
    cache_file = os.path.join(CACHE_DIR, f"{safe_symbol}.csv")

    if os.path.exists(cache_file):
        df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
        last_date = df.index.max().date()
        today = datetime.utcnow().date()

        if last_date < today:
            new_df = yf.download(
                symbol,
                start=last_date + timedelta(days=1),
                progress=False
            )
            if not new_df.empty:
                df = pd.concat([df, new_df])
                df.to_csv(cache_file)

        return df

    df = yf.download(symbol, period=f"{lookback_days}d", progress=False)
    df.to_csv(cache_file)
    return df

def get_live_price(symbol):
    try:
        return yf.Ticker(symbol).info.get("regularMarketPrice")
    except:
        return None

# ========================
# Scan logic
# ========================
alerts = []

for symbol in symbols:
    try:
        df = get_price_data(symbol)

        if len(df) < 60:
            continue

        macd = MACD(df["Close"])
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()

        rsi = RSIIndicator(df["Close"]).rsi()
        df["rsi"] = rsi

        live_price = get_live_price(symbol)
        if live_price is None:
            continue

        one_month_return = live_price / df["Close"].iloc[-22] - 1

        buy_signal = (
            df["macd"].iloc[-2] < df["macd_signal"].iloc[-2] and
            df["macd"].iloc[-1] > df["macd_signal"].iloc[-1] and
            df["rsi"].iloc[-2] > 30 and
            df["rsi"].iloc[-1] < 30 and
            one_month_return < -0.05
        )

        sell_signal = (
            df["macd"].iloc[-2] > df["macd_signal"].iloc[-2] and
            df["macd"].iloc[-1] < df["macd_signal"].iloc[-1] and
            df["rsi"].iloc[-2] < 70 and
            df["rsi"].iloc[-1] > 70 and
            one_month_return > 0.07
        )

        if buy_signal:
            alerts.append(
                f"🟢 BUY\n{symbol}\n1M return: {one_month_return:.1%}"
            )

        if sell_signal:
            alerts.append(
                f"🔴 SELL\n{symbol}\n1M return: {one_month_return:.1%}"
            )

    except Exception as e:
        print(f"{symbol} error: {e}")

# ========================
# Notify
# ========================
if alerts:
    send_alert("\n\n".join(alerts))
else:
    print("No signals this run")

send_alert("🧪 Test alert – Stock Scanner is working")
