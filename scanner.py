import os
import pandas as pd
import yfinance as yf
import requests
from ta.trend import MACD
from ta.momentum import RSIIndicator

# ========================
# Telegram configuration
# ========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN or CHAT_ID not found in environment variables")

def send_alert(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

# ========================
# Load symbols
# ========================
symbols_df = pd.read_excel("symbols.xlsx")
symbols = symbols_df.iloc[:, 0].dropna().tolist()

alerts = []

# ========================
# Scan each stock
# ========================
for symbol in symbols:
    try:
        df = yf.download(symbol, period="1y", interval="1d", progress=False)

        if len(df) < 60:
            continue

        # Indicators
        macd_ind = MACD(df["Close"])
        df["macd"] = macd_ind.macd()
        df["macd_signal"] = macd_ind.macd_signal()

        rsi_ind = RSIIndicator(df["Close"])
        df["rsi"] = rsi_ind.rsi()

        # 1-month return (~22 trading days)
        one_month_return = df["Close"].iloc[-1] / df["Close"].iloc[-22] - 1

        # BUY conditions
        buy_signal = (
            df["macd"].iloc[-2] < df["macd_signal"].iloc[-2] and
            df["macd"].iloc[-1] > df["macd_signal"].iloc[-1] and
            df["rsi"].iloc[-2] > 30 and
            df["rsi"].iloc[-1] < 30 and
            one_month_return < -0.05
        )

        # SELL conditions
        sell_signal = (
            df["macd"].iloc[-2] > df["macd_signal"].iloc[-2] and
            df["macd"].iloc[-1] < df["macd_signal"].iloc[-1] and
            df["rsi"].iloc[-2] < 70 and
            df["rsi"].iloc[-1] > 70 and
            one_month_return > 0.07
        )

        if buy_signal:
            alerts.append(
                f"🟢 BUY SIGNAL\n"
                f"{symbol}\n"
                f"1-month return: {one_month_return:.1%}"
            )

        if sell_signal:
            alerts.append(
                f"🔴 SELL SIGNAL\n"
                f"{symbol}\n"
                f"1-month return: {one_month_return:.1%}"
            )

    except Exception as e:
        print(f"{symbol} failed: {e}")

# ========================
# Send alerts
# ========================
if alerts:
    send_alert("\n\n".join(alerts))
else:
    print("No signals today")


