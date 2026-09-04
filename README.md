# RE-ZERO — Notifications téléphone sans Telegram

Cette version ajoute les notifications navigateur.

1. Dans la barre latérale, active « Notifications navigateur ».
2. Autorise les notifications dans le navigateur du téléphone.
3. Active « Surveillance intelligente ».
4. RE-ZERO déclenche une notification lorsqu’une opportunité passe les filtres existants.
5. La même opportunité n’est pas renotifiée à chaque rafraîchissement.

Important : les notifications navigateur fonctionnent lorsque la page RE-ZERO reste ouverte. Pour des notifications push même lorsque l’application est complètement fermée, il faudra ensuite mettre en place un vrai service Web Push/PWA avec un service worker.

# RE-ZERO RE-ZERO — Intelligent Macro + Orderflow Engine

RE-ZERO adds a decision layer combining multi-timeframe trend, inferred buyer/seller pressure, liquidity, momentum, volatility, Fibonacci and macro-event risk. It monitors public economic calendars such as the U.S. BLS Employment Situation (NFP) and Federal Reserve dates.

**Important:** the engine estimates pressure and setup quality; it does not predict economic releases with certainty, access hidden institutional orders, or guarantee profitable trades. High-impact events can block new setups rather than force entries.

Markets: EUR/USD, XAU/USD, BTC/USD.
Execution remains disabled: analyse → paper → demo → live.

# RE-ZERO / Irenee RE-ZERO Intelligence Core

AI market analyst for EUR/USD + XAU/USD + BTC/USD, designed around selective setups and risk control.

## RE-ZERO Intelligence Core additions
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


## RE-ZERO EUR/USD + XAU/USD + BTC/USD Trade Manager
Le projet est désormais centré exclusivement sur BTC/USD. Le moteur recherche des confluences de tendance, structure, liquidité, momentum, volatilité et R:R. Une seule position PAPER peut être active à la fois. Après validation de la prise de trade, le Trade Manager suit la position jusqu’à TP2 ou SL et n’autorise aucun nouveau signal d’entrée avant sa clôture. Le score de qualité n’est pas une probabilité de gain.

## RE-ZERO Intelligence Core
Cette version ajoute un détecteur de régime de marché, un audit de qualité des données, une décision hiérarchique qui traite la direction comme un scénario conditionnel et un moteur de validation statistique avec walk-forward, bootstrap, permutation et diagnostics par régime. Les métriques servent à détecter la fragilité et le surajustement, pas à garantir des gains.

## RE-ZERO dynamic timeframe release
- Execution timeframe: M5, M15, M30, H1, H4 or D1.
- The selected timeframe is preserved and drives a relative context/structure/setup/trigger policy.
- Liquidity is a first-class gate: visible pools, recent highs/lows, sweep, reclaim and displacement inference.
- Risk rules: R:R >= 1:2 and maximum 3 trades opened per day.
- Session controller displays active/closed state, remaining time and daily allowance.
- Browser notifications are permission-gated; Telegram can be enabled with `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` secrets.
- No broker order execution is enabled.

### Notification reality check
Browser notifications require HTTPS and permission. The Streamlit browser bridge can notify while the app is active. Reliable background push when the page is closed requires a real Web Push service worker/VAPID backend or an external channel such as Telegram. RE-ZERO does not pretend a JavaScript alert is a magic background push service.
