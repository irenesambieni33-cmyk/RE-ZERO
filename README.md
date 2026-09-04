# RE-ZERO RE-ZERO — Intelligent Macro + Orderflow Engine

RE-ZERO adds a decision layer combining multi-timeframe trend, inferred buyer/seller pressure, liquidity, momentum, volatility, Fibonacci and macro-event risk. It monitors public economic calendars such as the U.S. BLS Employment Situation (NFP) and Federal Reserve dates.

**Important:** the engine estimates pressure and setup quality; it does not predict economic releases with certainty, access hidden institutional orders, or guarantee profitable trades. High-impact events can block new setups rather than force entries.

Markets: EUR/USD, XAU/USD, BTC/USD.
Execution remains disabled: analyse → paper → demo → live.

# RE-ZERO / Irenee V5.3

AI market analyst for EUR/USD + XAU/USD + BTC/USD, designed around selective setups and risk control.

## V5.3 additions
- Setup Quality Engine (0-100, grades A+/A/B)
- Safety Gate with hard risk blockers
- Paper Trading ledger
- Professional M15 plan backtest with Entry/SL/TP, spread, slippage, fees and R-multiples
- Performance dashboard: trades, win rate, net R, profit factor, max drawdown, expectancy
- Market Timing Engine: configurable monitoring window + volatility regime + M15 activity score
- Automatic in-app monitoring with configurable refresh (30/60/120/300 s)
- Opportunity detector: signal + quality + safety + volatility window must align before alert
- Optional Telegram notifications through Streamlit Secrets

## Important
The score/confidence is not a guaranteed probability of winning. The system deliberately prefers `ATTENDRE` to forcing a trade.

Live broker execution remains disabled by default.

## Optional Telegram alerts
Add these values to Streamlit Secrets, never to GitHub:

```toml
TELEGRAM_BOT_TOKEN = "..."
TELEGRAM_CHAT_ID = "..."
```

The app sends a Telegram alert only when the opportunity detector validates direction, setup quality, Safety Gate and timing window together. It never sends a broker order.

## Streamlit
Entrypoint: `app.py`

`requirements.txt` must stay at repository root.


## V5.5 EUR/USD + XAU/USD + BTC/USD Trade Manager
Le projet est désormais centré exclusivement sur BTC/USD. Le moteur recherche des confluences de tendance, structure, liquidité, momentum, volatilité et R:R. Une seule position PAPER peut être active à la fois. Après validation de la prise de trade, le Trade Manager suit la position jusqu’à TP2 ou SL et n’autorise aucun nouveau signal d’entrée avant sa clôture. Le score de qualité n’est pas une probabilité de gain.
