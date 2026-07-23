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

# ------------------ api keys ------------------ #

load_dotenv("SECRETS.env")

alpaca_api_endpoint = os.getenv('ALPACA_API_ENDPOINT')
alpaca_api_key = os.getenv('ALPACA_API_KEY')
alpaca_secret = os.getenv('ALPACA_API_SECRET')

# ---------------------------------------------- #
def returnListOfStocks(trading_client):
    search_params = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)
    return list(trading_client.get_all_assets(search_params))

def findClosestAmount(data_client, symbol, amount):
    request = StockLatestTradeRequest(symbol_or_symbols=symbol)
    latest_trade = data_client.get_stock_latest_trade(request)

    price = latest_trade[symbol].price

    return amount // price

# ---------------------------------------------- #

os.system('clear')

trading_client = TradingClient(alpaca_api_key, alpaca_secret)
data_client = StockHistoricalDataClient(alpaca_api_key, alpaca_secret)
assets = returnListOfStocks(trading_client)

while True:
    try:
        positions = trading_client.get_all_positions()
        owned_symbols = {p.symbol for p in positions}

        cprint("Looking for stocks to buy...", "cyan")
        for asset in assets:
            if not (asset.tradable and asset.status == "active"):
                continue

            if asset.exchange not in {"NYSE", "NASDAQ", "AMEX"}:
                continue

            if asset.symbol not in owned_symbols:
                try:
                    cprint(f"Considering {asset.symbol}...", "grey")
                    if checkBuy(data_client, asset.symbol) == "buy":
                        # Buy $1000 worth
                        if asset.fractionable:
                            market_order_data = MarketOrderRequest(
                                symbol=asset.symbol,
                                notional="1000",
                                side=OrderSide.BUY,
                                time_in_force=TimeInForce.DAY
                            )
                            trading_client.submit_order(market_order_data)
                            cprint(f"BUY order submitted for {asset.symbol} worth $1000", "green")
                        else:
                            amount = findClosestAmount(data_client, asset.symbol, 1000)
                            market_order_data = MarketOrderRequest(
                                symbol=asset.symbol,
                                qty=amount,
                                side=OrderSide.BUY,
                                time_in_force=TimeInForce.DAY
                            )
                            trading_client.submit_order(market_order_data)
                            cprint(f"BUY order submitted for {amount} shares {asset.symbol} worth $1000", "green")
                except Exception as e:
                    cprint(f"Error processing {asset.symbol}: {e}", "red")

        cprint("Looking for stocks to sell...", "cyan")
        for position in positions:
            try:
                if checkSell(data_client, position.symbol) == "sell":
                    # Sell all shares
                    market_order_data = MarketOrderRequest(
                        symbol=position.symbol,
                        qty=position.qty,
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.DAY
                    )
                    trading_client.submit_order(market_order_data)
                    cprint(f"SELL order submitted for all shares of {position.symbol}", "red")
            except Exception as e:
                cprint(f"Error processing {position.symbol}: {e}", "red")

    except Exception as e:
        cprint(f"Loop error: {e}", "red")

    time.sleep(60)
