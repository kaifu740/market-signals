import os
import yfinance as yf
import pandas as pd
import datetime
import requests

TICKERS = os.getenv("TICKERS", "RELIANCE.NS,INFY.NS,TCS.NS").split(",")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def sma_signals(df, short=20, long=50):
    df = df.copy()
    df['SMA_short'] = df['Close'].rolling(short).mean()
    df['SMA_long'] = df['Close'].rolling(long).mean()
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    signal = None
    
    if latest['SMA_short'] > latest['SMA_long'] and prev['SMA_short'] <= prev['SMA_long']:
        signal = "BUY"
    elif latest['SMA_short'] < latest['SMA_long'] and prev['SMA_short'] >= prev['SMA_long']:
        signal = "SELL"

    return signal, latest, prev

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not set.")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        resp = requests.post(url, data=payload, timeout=10)
        print("Telegram sent:", resp.status_code)
    except Exception as e:
        print("Telegram error:", e)

def analyze_one(ticker):
    try:
        df = yf.download(ticker, period="120d", interval="1d", progress=False)
        if df.empty or len(df) < 60:
            return None
        
        signal, latest, prev = sma_signals(df)
        
        if not signal:
            return None

        msg = (
            f"{ticker}\n"
            f"Close: {latest['Close']:.2f}\n"
            f"SMA20: {latest['SMA_short']:.2f}\n"
            f"SMA50: {latest['SMA_long']:.2f}\n"
            f"Signal: {signal}"
        )
        return msg

    except Exception as e:
        print(f"Error for {ticker}: {e}")
        return None

def main():
    messages = []
    
    for t in TICKERS:
        t = t.strip()
        res = analyze_one(t)
        if res:
            messages.append(res)
    
    if not messages:
        print("No signals today.")
        return
    
    full_msg = (
        "Daily Market Signals\n\n" +
        "\n\n".join(messages)
    )

    send_telegram(full_msg)

if __name__ == "__main__":
    main()
