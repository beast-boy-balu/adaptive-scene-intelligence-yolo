import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Stock Intelligence Dashboard", layout="wide")

st.title("📈 Real-Time Stock Intelligence System")

# ----------------------------
# SIDEBAR INPUT
# ----------------------------
st.sidebar.header("Settings")

tickers_input = st.sidebar.text_input(
    "Enter Stock Tickers (Example: RELIANCE.NS,TCS.NS)"
)

fy_input = st.sidebar.text_input(
    "Financial Year Start (Example: 2022 for FY 2022-23)"
)

if tickers_input.strip() == "":
    st.info("Enter stock tickers in the sidebar.")
    st.stop()

tickers = [t.strip() for t in tickers_input.split(",")]

# ----------------------------
# FINANCIAL YEAR
# ----------------------------
use_fy = False
if fy_input.isdigit():
    fy = int(fy_input)
    start_date = f"{fy}-04-01"
    end_date = f"{fy+1}-03-31"
    use_fy = True

# ----------------------------
# STOCK NAME
# ----------------------------
def get_stock_name(ticker):
    try:
        return yf.Ticker(ticker).info.get("longName", ticker)
    except:
        return ticker

stock_names = {t: get_stock_name(t) for t in tickers}

# ----------------------------
# DATA FUNCTIONS
# ----------------------------
def fetch_live_data(stock):
    return yf.Ticker(stock).history(period="1d", interval="1m")

def fetch_fy_data(stock):

    if not use_fy:
        return None

    data = yf.download(stock, start=start_date, end=end_date, interval="1d", progress=False)

    if data.empty:
        return None

    data.reset_index(inplace=True)

    data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]

    return data

# ----------------------------
# BUY / SELL SIGNALS
# ----------------------------
def add_signals(data):

    data = data.copy()

    data["MA5"] = data["Close"].rolling(5).mean()
    data["MA20"] = data["Close"].rolling(20).mean()

    data["Signal"] = 0
    data.loc[data["MA5"] > data["MA20"], "Signal"] = 1
    data.loc[data["MA5"] < data["MA20"], "Signal"] = -1

    data["Position"] = data["Signal"].diff()

    return data

# ============================
# EACH STOCK ANALYSIS
# ============================
for stock in tickers:

    st.header(stock_names.get(stock, stock))

    live_data = fetch_live_data(stock)

    if live_data.empty:
        st.warning("No data available")
        continue

    latest = live_data.iloc[-1]

    # -------------------------
    # 1 OHLCV
    # -------------------------
    st.subheader("OHLCV Data")

    c1,c2,c3,c4,c5 = st.columns(5)

    c1.metric("Open", round(latest["Open"],2))
    c2.metric("High", round(latest["High"],2))
    c3.metric("Low", round(latest["Low"],2))
    c4.metric("Close", round(latest["Close"],2))
    c5.metric("Volume", int(latest["Volume"]))

    # -------------------------
    # 2 LIVE TRACKING
    # -------------------------
    st.subheader("Live Stock Tracking")

    fig_live = go.Figure()

    fig_live.add_trace(go.Scatter(
        x=live_data.index,
        y=live_data["Close"],
        name="Live Price"
    ))

    fig_live.update_layout(
        height=400,
        xaxis_title="Time",
        yaxis_title="Price"
    )

    st.plotly_chart(fig_live, use_container_width=True)

    # -------------------------
    # 3 BUY / SELL SIGNALS
    # -------------------------
    st.subheader("Buy / Sell Signals")

    signal_data = add_signals(live_data)

    buy = signal_data[signal_data["Position"] > 0]
    sell = signal_data[signal_data["Position"] < 0]

    fig_signal = go.Figure()

    fig_signal.add_trace(go.Scatter(
        x=signal_data.index,
        y=signal_data["Close"],
        name="Close Price"
    ))

    fig_signal.add_trace(go.Scatter(
        x=signal_data.index,
        y=signal_data["MA5"],
        name="MA5"
    ))

    fig_signal.add_trace(go.Scatter(
        x=signal_data.index,
        y=signal_data["MA20"],
        name="MA20"
    ))

    fig_signal.add_trace(go.Scatter(
        x=buy.index,
        y=buy["Close"],
        mode="markers",
        marker=dict(color="green", size=10),
        name="BUY"
    ))

    fig_signal.add_trace(go.Scatter(
        x=sell.index,
        y=sell["Close"],
        mode="markers",
        marker=dict(color="red", size=10),
        name="SELL"
    ))

    fig_signal.update_layout(height=450)

    st.plotly_chart(fig_signal, use_container_width=True)

    # -------------------------
    # 4 FINANCIAL YEAR TREND
    # -------------------------
    if use_fy:

        st.subheader(f"Financial Year Trend (FY {fy}-{fy+1})")

        fy_data = fetch_fy_data(stock)

        if fy_data is None:
            st.warning("No financial year data available")
        else:

            fig_fy = go.Figure()

            fig_fy.add_trace(go.Candlestick(
                x=fy_data["Date"],
                open=fy_data["Open"],
                high=fy_data["High"],
                low=fy_data["Low"],
                close=fy_data["Close"]
            ))

            fig_fy.update_layout(
                height=500,
                xaxis_title="Date",
                yaxis_title="Price",
                xaxis_rangeslider_visible=False
            )

            st.plotly_chart(fig_fy, use_container_width=True)

# ============================
# 5 STOCK COMPARISON
# ============================

st.subheader("Stock Comparison (Single Plot)")

data = yf.download(
    tickers,
    period="1mo",
    interval="1d",
    progress=False
)

if not data.empty:

    fig_compare = go.Figure()

    for stock in tickers:

        fig_compare.add_trace(go.Scatter(
            x=data.index,
            y=data["Close"][stock],
            mode="lines",
            name=stock
        ))

    fig_compare.update_layout(
        title="Stock Price Comparison",
        xaxis_title="Date",
        yaxis_title="Close Price",
        height=500
    )

    st.plotly_chart(fig_compare, use_container_width=True)

else:
    st.warning("Not enough data for comparison")

st.write("Last Updated:", datetime.now().strftime("%H:%M:%S"))