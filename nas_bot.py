import os
import sys
import requests
import numpy as np
import pandas as pd
import yfinance as yf

# GitHub will safely inject your secret URL into this environment variable
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL == "YOUR_COPIED_WEBHOOK_URL_FROM_DISCORD":
    print("❌ Critical Error: DISCORD_WEBHOOK secret environment variable is missing!")
    sys.exit(1)

TARGET_ASSET = "^NDX"

def send_discord_alert(message):
    payload = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code != 204:
            print(f"⚠️ Discord responded with code: {response.status_code}")
    except Exception as e:
        print(f"❌ Network Error: {e}")

def fetch_live_market_data():
    try:
        ticker = yf.Ticker(TARGET_ASSET)
        df_1h = ticker.history(period="3mo", interval="1h")
        if df_1h.empty: return None
        
        df_4h = df_1h.resample('4H').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'
        }).dropna()
        df_4h.columns = [col.lower() for col in df_4h.columns]
        return df_4h
    except Exception as e:
        print(f"Data Error: {e}")
        return None

def calculate_lsma(series, period=70):
    def lr(window):
        x = np.arange(len(window))
        slope, intercept = np.polyfit(x, window, 1)
        return slope * (len(window) - 1) + intercept
    return series.rolling(window=period).apply(lr, raw=True)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / loss)))

def execute_strategy_scan():
    df = fetch_live_market_data()
    if df is None or len(df) < 75: 
        print("⚠️ Data array incomplete.")
        return
        
    df['lsma'] = calculate_lsma(df['close'], 70)
    df['rsi'] = calculate_rsi(df['close'], 14)
    df['slope'] = df['lsma'] - df['lsma'].shift(1)
    
    current_close, prev_close = df['close'].iloc[-1], df['close'].iloc[-2]
    current_lsma, prev_lsma = df['lsma'].iloc[-1], df['lsma'].iloc[-2]
    current_rsi, current_slope = df['rsi'].iloc[-1], df['slope'].iloc[-1]
    
    print(f" Nasdaq Close: {current_close:.2f} | LSMA: {current_lsma:.2f} | RSI: {current_rsi:.2f}")
    
    is_crossover = (prev_close <= prev_lsma) and (current_close > current_lsma)
    is_crossunder = (prev_close >= prev_lsma) and (current_close < current_lsma)
    
    if is_crossover and current_slope > 0 and current_rsi > 53:
        send_discord_alert(f"🚀 **[STRATEGY LONG]**\nAsset: NAS100 (4H)\nPrice crossed ABOVE LSMA 70.\nRSI is strong at {current_rsi:.1f}.\n👉 *Open Match-Trader and look for Buys.*")
    elif is_crossunder and current_slope < 0 and current_rsi < 47:
        send_discord_alert(f"📉 **[STRATEGY SHORT]**\nAsset: NAS100 (4H)\nPrice crossed BELOW LSMA 70.\nRSI is weak at {current_rsi:.1f}.\n👉 *Open Match-Trader and look for Sells.*")

if __name__ == "__main__":
    execute_strategy_scan()
def send_discord_alert(message):
    payload = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        # This will print the error in your GitHub Action logs if Discord rejects the link
        if response.status_code != 204:
            print(f"⚠️ DISCORD ERROR: Status {response.status_code}, Response: {response.text}")
        else:
            print("✅ Successfully sent message to Discord!")
    except Exception as e:
        print(f"❌ Network Error: {e}")
if __name__ == "__main__":
    execute_strategy_scan()
    # This line triggers the alert so you can see it in Discord
    send_discord_alert("🤖 Bot Heartbeat: System is online and monitoring!")
