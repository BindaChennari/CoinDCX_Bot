# utils.py

import requests
import pandas as pd
import ta
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, RSI_OVERSOLD, RSI_OVERBOUGHT

def fetch_candles(symbol, interval_minutes=15, limit=100):
    url = f"https://public.coindcx.com/market_data/candles?pair={symbol}&interval={interval_minutes}m&limit={limit}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = response.json()
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["close"] = pd.to_numeric(df["close"])
    df["high"] = pd.to_numeric(df["high"])
    df["low"] = pd.to_numeric(df["low"])
    return df

def calculate_indicators(df):
    df["rsi"] = ta.momentum.RSIIndicator(close=df["close"], window=14).rsi()
    macd = ta.trend.MACD(close=df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    # 🟡 For now, we'll just create a dummy 'supertrend' based on MACD trend
    df["supertrend"] = df["macd"] - df["macd_signal"]
    return df

def check_signal(df):
    latest = df.iloc[-1]

    # Logic
    trend_up = latest["supertrend"] > 0
    macd_cross = latest["macd"] > latest["macd_signal"]
    rsi_low = latest["rsi"] < RSI_OVERSOLD
    rsi_high = latest["rsi"] > RSI_OVERBOUGHT

    if trend_up and macd_cross and rsi_low:
        return "BUY"
    elif not trend_up and not macd_cross and rsi_high:
        return "SELL"
    return None

def send_telegram_alert(symbol, signal, price, rsi, macd, supertrend):
    message = (
        f"📢 *{signal} Signal Detected!*\n\n"
        f"🪙 *Pair:* `{symbol}`\n"
        f"💰 *Price:* ₹{price:.2f}\n"
        f"📊 *RSI:* {rsi:.2f}\n"
        f"📈 *MACD:* {macd:.4f}\n"
        f"📉 *Supertrend:* {supertrend:.4f}\n\n"
        f"#CoinDCX #TradingBot"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Telegram Error:", e)
