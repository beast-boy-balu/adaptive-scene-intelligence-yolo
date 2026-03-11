import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import time
from datetime import datetime

# -----------------------------
# STOCK INPUT
# -----------------------------
tickers_input = input("Enter stock tickers (example: RELIANCE.NS,TCS.NS): ")
tickers = [t.strip() for t in tickers_input.split(",") if t.strip()]

# -----------------------------
# GET STOCK FULL NAME
# -----------------------------
def get_stock_name(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get("longName", ticker)
    except:
        return ticker

stock_names = {t:get_stock_name(t) for t in tickers}

# -----------------------------
# FINANCIAL YEAR INPUT (optional)
# -----------------------------
fy_input = input("Enter financial year start (example: 2023 for FY 2023-24) or press Enter for live only: ").strip()

if fy_input.isdigit():
    fy = int(fy_input)
    start_date = f"{fy}-04-01"
    end_date = f"{fy+1}-03-31"
    use_fy = True
else:
    use_fy = False

# -----------------------------
# GRAPH SETUP
# -----------------------------
plt.ion()
fig, (ax1, ax2) = plt.subplots(2,1, figsize=(12,8))

# -----------------------------
# FETCH FINANCIAL YEAR DATA
# -----------------------------
def fetch_fy_data():
    fy_data = {}
    if not use_fy:
        return fy_data
    for stock in tickers:
        try:
            data = yf.download(stock, start=start_date, end=end_date, interval="1d")
            if not data.empty:
                fy_data[stock] = data
        except Exception as e:
            print("Error:", stock, e)
    return fy_data

# -----------------------------
# FETCH LIVE DATA
# -----------------------------
def fetch_live_data():
    live_data = {}
    for stock in tickers:
        try:
            data = yf.Ticker(stock).history(period="1d", interval="1m")
            if not data.empty:
                live_data[stock] = data
        except Exception as e:
            print("Live error:", stock, e)
    return live_data

# -----------------------------
# PRINT OHLCV
# -----------------------------
def print_ohlcv(live_data):
    print("\n====== STOCK OHLCV DATA ======")

    for stock, data in live_data.items():

        latest = data.iloc[-1]

        print(f"\nStock Name : {stock_names.get(stock,stock)}")
        print(f"Ticker     : {stock}")
        print(f"Time       : {datetime.now().strftime('%H:%M:%S')}")
        print(f"Open       : {latest['Open']}")
        print(f"High       : {latest['High']}")
        print(f"Low        : {latest['Low']}")
        print(f"Close      : {latest['Close']}")
        print(f"Volume     : {latest['Volume']}")

# -----------------------------
# ADD BUY / SELL SIGNALS
# -----------------------------
def add_signals(data):

    data = data.copy()

    data['MA5'] = data['Close'].rolling(5).mean()
    data['MA20'] = data['Close'].rolling(20).mean()

    data['Signal'] = 0
    data.loc[data['MA5'] > data['MA20'], 'Signal'] = 1
    data.loc[data['MA5'] < data['MA20'], 'Signal'] = -1

    data['Position'] = data['Signal'].diff()

    return data

# -----------------------------
# PLOT FUNCTION
# -----------------------------
def plot_data(fy_data, live_data):

    ax1.clear()
    ax2.clear()

    # LIVE TRACKING
    for stock, data in live_data.items():

        ax1.plot(data.index,
                 data['Close'],
                 label=f"{stock_names.get(stock,stock)}")

    ax1.set_title("Live Stock Tracking")
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Price")
    ax1.legend()
    ax1.grid(True)

    # BUY SELL SIGNAL
    for stock in tickers:

        frames = []

        if use_fy and stock in fy_data:
            frames.append(fy_data[stock])

        if stock in live_data:
            frames.append(live_data[stock])

        if frames:

            data = pd.concat(frames)

            data = add_signals(data)

            buy = data[data['Position'] > 0]
            sell = data[data['Position'] < 0]

            ax2.plot(data.index,
                     data['Close'],
                     label=f"{stock_names.get(stock,stock)} Close")

            ax2.plot(data.index,
                     data['MA5'],
                     '--',
                     label=f"{stock_names.get(stock,stock)} MA5")

            ax2.plot(data.index,
                     data['MA20'],
                     '--',
                     label=f"{stock_names.get(stock,stock)} MA20")

            ax2.scatter(buy.index,
                        buy['Close'],
                        marker='^',
                        color='green',
                        s=100,
                        label=f"{stock_names.get(stock,stock)} BUY")

            ax2.scatter(sell.index,
                        sell['Close'],
                        marker='v',
                        color='red',
                        s=100,
                        label=f"{stock_names.get(stock,stock)} SELL")

    ax2.set_title(f"Buy / Sell Signals{' (FY ' + str(fy) + '-' + str(fy+1) + ')' if use_fy else ''}")
    ax2.set_xlabel("Date / Time")
    ax2.set_ylabel("Price")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.pause(0.01)

# -----------------------------
# LOAD FY DATA
# -----------------------------
fy_data = fetch_fy_data()

# -----------------------------
# LIVE LOOP
# -----------------------------
while True:

    try:

        live_data = fetch_live_data()

        if live_data:
            print_ohlcv(live_data)
            plot_data(fy_data, live_data)

        time.sleep(60)

    except KeyboardInterrupt:
        print("Program stopped")
        break