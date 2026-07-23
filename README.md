# macd-bot

An automated trading bot built on the [Alpaca](https://alpaca.markets/) API. It scans US equities on a loop, buying and selling based on a moving-average crossover confirmed by RSI, and includes a standalone backtester to evaluate the strategy against historical data before risking real money.

## Strategy

For each symbol, `moving_average.py` pulls recent daily bars and computes:

- **20-day** and **50-day** simple moving averages (SMA)
- **14-day RSI**

**Buy** when the 20-day SMA crosses above the 50-day SMA and RSI is below 65 (avoids chasing overbought moves).

**Sell** when RSI rises above 70 (overbought), or the 20-day SMA drops below the 50-day SMA while the market has fallen since 50 bars ago.

## Project structure

| File | Purpose |
|---|---|
| `main.py` | Live/paper trading loop — scans all tradable US equities, places buy/sell orders via Alpaca |
| `moving_average.py` | Strategy logic (`checkBuy` / `checkSell`) shared by the live bot and backtester |
| `backtester.py` | Runs the strategy over historical data for a fixed watchlist and compares returns to SPY |
| `test.py` | Quick sanity check for terminal color output |

## Setup

1. Clone the repo and install dependencies:

   ```bash
   git clone https://github.com/NecirvanA/macd-bot.git
   cd macd-bot
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `SECRETS.env` and fill in your [Alpaca API keys](https://app.alpaca.markets/paper/dashboard/overview):

   ```bash
   cp .env.example SECRETS.env
   ```

   ```env
   ALPACA_API_ENDPOINT=https://paper-api.alpaca.markets
   ALPACA_API_KEY=your_api_key_here
   ALPACA_API_SECRET=your_api_secret_here
   ```

   `SECRETS.env` is gitignored — never commit real API keys. Use Alpaca's **paper trading** endpoint unless you specifically intend to trade live.

## Usage

**Run the live/paper trading loop:**

```bash
python main.py
```

Scans every tradable NYSE/NASDAQ/AMEX equity each minute, buying $1,000 worth of a symbol when a buy signal fires and selling full positions on a sell signal.

**Run the backtester:**

```bash
python backtester.py
```

Backtests a fixed watchlist of large-cap symbols over the past year, starting from $100,000, and prints profit per symbol plus a comparison against buy-and-hold SPY returns.

## Disclaimer

This is a personal/educational project, not financial advice. Trading involves risk of loss. Test thoroughly with a paper trading account before ever pointing this at a live account, and use it entirely at your own risk.
# macd-bot
