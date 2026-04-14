# Integer Portfolio Optimization — OPIM 5641

MINLP portfolio optimizer built on the Womack example, extended with:
- Live market data via `yfinance`
- Dynamic sector classification
- 8-constraint MINLP model (Bonmin solver)
- Maximum Sharpe Ratio selection
- Automated daily 3:55 PM price capture via GitHub Actions

## Repo Structure

```
.github/workflows/price_capture.yml  ← cron scheduler (runs on GitHub, free)
capture_prices.py                    ← price capture script
data/prices_3pm55.csv                ← grows by one row every trading day at 3:55 PM ET
Integer_Portfolio_LiveData_Extended.ipynb  ← main notebook (run in Colab)
```

## Setup

1. Fork or push this repo to your GitHub account
2. Actions are enabled by default on public repos
3. Open the notebook in Colab, set `GITHUB_USER` and `GITHUB_REPO` in Step 10
4. Run `rebuild_returns_from_github()` at the start of each session to load fresh data

## Running the Optimizer

Run all cells top to bottom in Colab. Bonmin is installed automatically via IDAES.  
The frontier sweep takes ~2–5 minutes depending on the number of risk levels.

## Manually Testing the Price Capture

Go to `Actions → Daily 3:55 PM Price Capture → Run workflow`.  
The run log shows exactly which prices were captured and whether the CSV was updated.
