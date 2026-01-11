import pandas as pd
import yfinance as yf
from ta.trend import MACD
from ta.momentum import RSIIndicator
import requests

send_alert("✅ Secrets loaded successfully")

BOT_TOKEN = "8202448416:AAGKBE87ejd8d-cXg7nJuUCGDTORw3a-7ps"
CHAT_ID = "553467603"

def send_alert(msg):
    url = f"https://api.telegram.org/bot8202448416:AAGKBE87ejd8d-cXg7nJuUCGDTORw3a-7ps/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

symbols = pd.read_excel("symbols.xlsx")["symbol"].tolist()

alerts = []

for symbol in symbols:
    try:
        df = yf.download(symbol, period="1y", interval="1d", progress=False)
        if len(df) < 50:
            continue

        macd = MACD(df["Close"])
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()

        rsi = RSIIndicator(df["Close"]).rsi()
        df["rsi"] = rsi

        one_month_return = df["Close"].iloc[-1] / df["Close"].iloc[-22] - 1

        buy = (
            df["macd"].iloc[-2] < df["macd_signal"].iloc[-2] and
            df["macd"].iloc[-1] > df["macd_signal"].iloc[-1] and
            df["rsi"].iloc[-2] > 30 and
            df["rsi"].iloc[-1] < 30 and
            one_month_return < -0.05
        )

        sell = (
            df["macd"].iloc[-2] > df["macd_signal"].iloc[-2] and
            df["macd"].iloc[-1] < df["macd_signal"].iloc[-1] and
            df["rsi"].iloc[-2] < 70 and
            df["rsi"].iloc[-1] > 70 and
            one_month_return > 0.07
        )

        if buy:
            alerts.append(f"🟢 BUY signal: {symbol}")
        elif sell:
            alerts.append(f"🔴 SELL signal: {symbol}")

    except Exception as e:
        print(symbol, e)

if alerts:

    send_alert("\n".join(alerts))

