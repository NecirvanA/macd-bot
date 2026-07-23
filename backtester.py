import os
from dotenv import load_dotenv

from alpaca.data.historical import *
from alpaca.data.requests import *
from alpaca.data.timeframe import *
from alpaca.trading.enums import *
from alpaca.trading.client import *
from alpaca.trading.requests import *

import time
from threading import Thread
from moving_average import checkBuy, checkSell

import sys
from termcolor import colored, cprint

from datetime import datetime, timedelta, timezone

# ------------------------------------------------- #

load_dotenv("SECRETS.env")

alpaca_api_endpoint = os.getenv('ALPACA_API_ENDPOINT')
alpaca_api_key = os.getenv('ALPACA_API_KEY')
alpaca_secret = os.getenv('ALPACA_API_SECRET')

# ------------------------------------------------- #

START_CASH = 100_000
TRADE_SIZE = 1000
LOOKBACK_DAYS = 365

SYMBOLS = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "GOOGL", # Alphabet (Class A)
    "AMZN",  # Amazon
    "META",  # Meta Platforms (Facebook)
    "TSLA",  # Tesla
    "NVDA",  # NVIDIA
    "BRK.B", # Berkshire Hathaway (Class B)
    "JPM",   # JPMorgan Chase
    "V",     # Visa
    "MA",    # Mastercard
    "UNH",   # UnitedHealth Group
    "HD",    # Home Depot
    "KO",    # Coca-Cola
    "PEP",   # PepsiCo
    "PFE",   # Pfizer
    "MRK",   # Merck
    "ABT",   # Abbott Laboratories
    "DIS",   # Disney
    "NFLX",  # Netflix
    "INTC",  # Intel
    "CSCO",  # Cisco
    "ADBE",  # Adobe
    "ORCL",  # Oracle
    "CRM",   # Salesforce
    "BA",    # Boeing
    "NKE",   # Nike
    "MCD",   # McDonald's
    "WMT",   # Walmart
    "T"      # AT&T
]


# ----------------------- UTIL -------------------- #

def get_bars(symbol, client):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=LOOKBACK_DAYS)

    req = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        feed=DataFeed.IEX
    )

    df = client.get_stock_bars(req).df
    if df.empty:
        return None

    return df.reset_index()

# ------------------- BACKTESTER ------------------ #

def backtest(symbol, client):
    bars = get_bars(symbol, client)
    if bars is None:
        cprint(f"{symbol}: no data", 'red')
        return None

    cash = START_CASH
    position = 0
    current_invested = 0          # cash currently in positions
    total_invested = 0            # max cash deployed at any time
    trades = []

    for i in range(len(bars)):
        price = bars["close"].iloc[i]
        date = bars["timestamp"].iloc[i]

        # BUY
        if position == 0 and cash >= TRADE_SIZE:
            if i < 50:
                continue

            if checkBuy(client, symbol, bars.iloc[:i+1]) == "buy":
                shares = int(TRADE_SIZE // price)
                cost = shares * price

                if shares > 0 and cost <= cash:
                    position = shares
                    cash -= cost
                    current_invested = cost
                    total_invested = max(total_invested, current_invested)
                    trades.append(("BUY", date, price, shares))
                    cprint(f"BUY {symbol} @ {price}", "green")

        # SELL
        elif position > 0:
            if i < 50:
                continue

            if checkSell(client, symbol, bars.iloc[:i+1]) == "sell":
                cash += position * price
                trades.append(("SELL", date, price, position))
                position = 0
                current_invested = 0
                cprint(f"SELL {symbol} @ {price}", "red")

    # Liquidate at end
    if position > 0:
        cash += position * bars["close"].iloc[-1]
        current_invested = 0

    return {
        "symbol": symbol,
        "final_cash": round(cash, 2),
        "profit": round(cash - START_CASH, 2),
        "invested": round(total_invested, 2),  # max deployed cash
        "trades": trades,
        "start_date": bars["timestamp"].iloc[0],
        "end_date": bars["timestamp"].iloc[-1]
    }




# ----------------- SPY BENCHMARK ----------------- #

def spy_performance(client, start, end, capital):
    request = StockBarsRequest(
        symbol_or_symbols="SPY",
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        feed=DataFeed.IEX
    )

    df = client.get_stock_bars(request).df
    if df.empty:
        return "N/A"
    
    df = df.reset_index()
    start_price = df["close"].iloc[0]
    end_price = df["close"].iloc[-1]

    pct_return = (end_price - start_price) / start_price
    dollar_return = capital * pct_return

    return round(pct_return * 100, 2), round(dollar_return, 2)


# --------------------------------------------------- #

results = []
total_profit = 0
total_invested = 0  # This will be the sum of max deployed capital across symbols

start_date = None
end_date = None

client = StockHistoricalDataClient(alpaca_api_key, alpaca_secret)

print("\n===== STRATEGY RESULTS =====\n")

for symbol in SYMBOLS:
    result = backtest(symbol, client)
    if result:
        results.append(result)
        total_profit += result["profit"]
        # total_invested now tracks sum of max invested per symbol
        total_invested += result["invested"]

        print(
            f"{symbol}: "
            f"Profit ${result['profit']} | "
            f"Max Invested ${result['invested']} | "
            f"Trades {len(result['trades']) // 2}"
        )

        # Capture overall start and end date for SPY comparison
        if start_date is None:
            start_date = result["start_date"]
            end_date = result["end_date"]

print("\n==============================")
print(f"TOTAL MAX INVESTED CAPITAL: ${round(total_invested, 2)}")
print(f"TOTAL STRATEGY PROFIT:  ${round(total_profit, 2)}")

# Compare to SPY using the same capital
spy = spy_performance(client, start_date, end_date, total_invested)
if spy:
    spy_pct, spy_dollars = spy
    print(f"SPY RETURN: {spy_pct}%")
    print(f"SPY PROFIT (same capital): ${spy_dollars}")

print("==============================\n")
