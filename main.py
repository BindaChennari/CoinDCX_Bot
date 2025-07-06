# main.py

import time
import requests
from utils import (
    fetch_candles,
    calculate_indicators,
    check_signal,
    send_telegram_alert
)
from config import INTERVAL_MINUTES

def get_inr_pairs():
    url = "https://api.coindcx.com/exchange/v1/markets_details"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()

        # ✅ Filter where base is INR
        return [x["symbol"] for x in data if x["base_currency_short_name"] == "INR"]
    except Exception as e:
        print("❌ Error fetching INR pairs:", e)
        return []

def main_loop():
    while True:
        print("⏳ Scanning CoinDCX INR pairs...")
        inr_pairs = get_inr_pairs()
        scanned = 0

        for symbol in inr_pairs:
            try:
                df = fetch_candles(symbol, interval_minutes=INTERVAL_MINUTES)
                if df is None or df.empty:
                    continue

                df = calculate_indicators(df)
                signal = check_signal(df)

                if signal:
                    latest = df.iloc[-1]
                    send_telegram_alert(
                        symbol=symbol,
                        signal=signal,
                        price=latest["close"],
                        rsi=latest["rsi"],
                        macd=latest["macd"],
                        supertrend=latest["supertrend"]
                    )
            except Exception as e:
                print(f"[{symbol}] Error: {str(e)}")

            scanned += 1
            if scanned % 10 == 0:
                print(f"Scanned {scanned} pairs...")

        print("✅ One full scan complete. Waiting for next cycle...\n")
        time.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    main_loop()
