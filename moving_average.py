from datetime import datetime, timedelta, timezone
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

# ---------------- DATA ---------------- #

def get_bars(symbol, client, lookback_days=60):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=lookback_days)

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

# ---------------- INDICATORS ---------------- #

def find_rsi(bars, period=14):
    delta = bars["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))

# ---------------- STRATEGY ---------------- #

def checkBuy(client, ticker, bars=None):
    """
    Live trading:
        checkBuy(client, "AAPL")

    Backtesting:
        checkBuy(client, "AAPL", bars)
    """

    if bars is None:
        bars = get_bars(ticker, client, lookback_days=60)

    if bars is None or len(bars) < 50:
        return "N/A"

    latest_close = bars["close"].iloc[-1]
    short_ma = bars["close"].tail(20).mean()
    long_ma = bars["close"].tail(50).mean()
    rsi = find_rsi(bars).iloc[-1]

    if short_ma > long_ma and rsi < 65:
        return "buy"

    return "N/A"


def checkSell(client, ticker, bars=None):
    """
    Live trading:
        checkSell(client, "AAPL")

    Backtesting:
        checkSell(client, "AAPL", bars)
    """

    if bars is None:
        bars = get_bars(ticker, client, lookback_days=60)

    if bars is None or len(bars) < 50:
        return "N/A"

    short_ma = bars["close"].tail(20).mean()
    long_ma = bars["close"].tail(50).mean()
    rsi = find_rsi(bars).iloc[-1]

    if rsi > 70:
        return "sell"

    if short_ma < long_ma and long_ma < bars["close"].iloc[-51]:
        return "sell"

    return "N/A"
