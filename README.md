# Meridian Capital · Integer Portfolio Optimizer

**OPIM 5641 — Business Decision Modeling · University of Connecticut · Spring 2026**

A production-grade Mixed-Integer Nonlinear Programming (MINLP) portfolio optimizer built on Modern Portfolio Theory. Screens 36 large-cap candidates through a two-stage RSI and return filter, solves the maximum-Sharpe allocation under 8 institutional-grade business constraints using Bonmin, and runs live daily via GitHub Actions. Extended with a five-model comparative suite and an AI-powered investment analysis layer.

---

## What This Project Does

The core model is a MINLP portfolio optimizer formulated in Pyomo and solved by COIN-OR Bonmin via IDAES. It selects exactly 10 stocks from a screened candidate pool, allocates weights between 5% and 40% per holding, enforces sector concentration limits, requires at least one defensive-sector stock, and traces the complete efficient frontier across 28 risk levels to identify the maximum-Sharpe portfolio.

Beyond the optimizer, the project includes:

- A two-stage pre-optimization screener (RSI + mean return floor)
- Dynamic sector classification pulled live from yfinance — no hardcoded mappings
- An out-of-sample backtest using a 12-month rolling training window vs SPY
- Five alternative allocation models for comparison: Equal Weight, Inverse Volatility, Hierarchical Risk Parity, SHAP-Weighted, and Momentum Tilt
- A walk-forward backtest comparing all models head-to-head
- A Claude API integration (Steps 12–14) that synthesizes results into an investment brief, structured JSON recommendation, and interactive Q&A
- A single-file HTML dashboard displaying all results live

---

## Repo Structure

```
.github/workflows/
  price_capture.yml                     ← cron job: 3:55 PM ET daily, Mon–Fri

data/
  prices_3pm55.csv                      ← growing daily price log (auto-committed)

Integer_Portfolio_LiveData_Extended.ipynb   ← main notebook (Steps 1–11)
Steps_12_13_14_Extension.ipynb             ← model comparison + Claude API (Steps 12–14)
capture_prices.py                          ← GitHub Actions price capture script
index.html                                 ← live reporting dashboard
README.md                                  ← this file
```

---

## Notebooks

### Main Notebook — Steps 1–11

Run in Google Colab. Installs Bonmin automatically via IDAES on first run.

| Step | What it does |
|------|-------------|
| 1    | Downloads 2 years of monthly returns for 36 candidate tickers via yfinance |
| 1b   | Screens candidates: 14-day Wilder RSI in [30, 70] and mean monthly return > 0 |
| 2    | Pulls live sector classifications from yfinance metadata |
| 3    | Summary statistics and covariance matrix heatmap |
| 4    | Constraint architecture documentation |
| 5    | Builds and solves the MINLP model for a single risk level |
| 6    | Sweeps 28 risk levels to trace the efficient frontier |
| 7    | Identifies the max-Sharpe portfolio |
| 8    | Post-solve constraint validation across all 28 solutions |
| 9    | Efficient frontier plot with integer discontinuity annotation |
| 10   | GitHub Actions integration — rebuilds return estimates from live CSV |
| 11   | Out-of-sample backtest: 12-month rolling window vs SPY |

### Extension Notebook — Steps 12–14

Appended to or run alongside the main notebook. Inherits `QUALIFIED_TICKERS`, `returns_df`, `df_cov`, and `sector_map` directly — no redundant data pulls.

| Step | What it does |
|------|-------------|
| 12   | Builds five alternative allocation models on the same screened ticker pool |
| 13   | Walk-forward backtest comparing all models + MINLP reference + SPY |
| 14   | Claude API integration: investment brief, JSON recommendation, multi-turn Q&A |

---

## The MINLP Model

**Decision variables:** `x[t]` — continuous allocation weight; `y[t]` — binary selection indicator

**Objective:** Maximize expected monthly return subject to a parametric variance ceiling

**Constraint architecture:**

| ID | Constraint | Formulation |
|----|-----------|-------------|
| C1 | Fully invested | `sum(x[t]) == 1` |
| C2a | Position cap | `x[t] <= 0.40 * y[t]` |
| C2b | Position floor | `x[t] >= 0.05 * y[t]` |
| C3 | Cardinality max | `sum(y[t]) <= 10` |
| C4 | Cardinality min | `sum(y[t]) >= 2` |
| C5 | Sector cap | `sum(x[t] for t in sector) <= 0.40` (dynamic) |
| C6 | Defensive floor | Must hold ≥ 1 Healthcare or Consumer Staples stock |
| C7 | Tech → Financials | If any Tech stock held, must also hold Financials |
| C8 | XOM / CVX exclusion | `y[XOM] + y[CVX] <= 1` |
| C9 | Risk ceiling | `sum(x[i] * COV[i,j] * x[j]) <= R` (swept parametrically) |

Zero constraint violations confirmed across all 28 frontier solutions.

---

## Alternative Models (Steps 12–13)

| Model | Core idea | Key property |
|-------|-----------|-------------|
| Equal Weight | 1/N | Zero estimation error, hard benchmark to beat consistently |
| Inverse Volatility | Weight by 1/σ | Low-vol assets absorb more capital; no covariance matrix needed |
| Hierarchical Risk Parity | Correlation clustering + recursive bisection | No matrix inversion — robust with many assets |
| SHAP-Weighted | Random Forest return predictor + SHAP importances as weights | Allocates by predictive explanatory power, not risk or return |
| Momentum Tilt | Rank by 12-1 month trailing return | Classic quant factor; capped at 20% per asset |

All five run through the same walk-forward backtest engine as the MINLP comparison (12-month training, 1-month out-of-sample, quarterly rebalance).

---

## Claude API Integration (Step 14)

Step 14 connects to the Anthropic API (`claude-sonnet-4`) and produces three outputs:

**Investment Brief** — 400–500 word plain-language synthesis of all model results, covering top performers, model differences, and a blended allocation recommendation.

**Structured JSON** — machine-parseable output including `recommended_model`, `risk_tier`, `suggested_blend`, `top_tickers`, `red_flags`, and `minlp_verdict`.

**Multi-turn Q&A** — conversation history preserved across calls. Full context (metrics, weights, brief) available so you can query the comparison interactively during a presentation.

To use Step 14, add your Anthropic API key as a Colab secret named `ANTHROPIC_API_KEY` (Secrets tab → key icon in the left sidebar).

---

## Live Data Pipeline

GitHub Actions runs `capture_prices.py` at 3:55 PM ET on every trading day (dual cron handles EDT/EST automatically). The script pulls current prices for all 36 candidate tickers, checks for NYSE holidays and duplicate rows, and appends a new row to `data/prices_3pm55.csv` with an auto-commit.

To rebuild your return estimates from the live CSV at the start of any Colab session:

```python
rebuild_returns_from_github()
```

To manually trigger a capture: `Actions → Daily 3:55 PM Price Capture → Run workflow`

Once you have ~22 trading days in the log, resample to monthly returns for compatibility with the optimizer:

```python
returns_monthly = (1 + returns_df).resample('ME').prod() - 1
```

---

## Setup

1. Fork this repo (keeps Actions running on your account)
2. In Colab, open `Integer_Portfolio_LiveData_Extended.ipynb`
3. Set `GITHUB_USER` and `GITHUB_REPO` in Step 10
4. Add a GitHub personal access token to Colab secrets as `GH_TOKEN`
5. Run all cells top to bottom — Bonmin installs automatically via IDAES (~2 min)
6. The frontier sweep takes 2–5 minutes depending on how many tickers passed screening

For the extension notebook (`Steps_12_13_14_Extension.ipynb`), run it in the same Colab session after the main notebook, or paste the cells directly after Step 11.

---

## Results (Most Recent Run — Apr 28, 2026)

| Metric | Value |
|--------|-------|
| Max Sharpe | 1.2736 |
| Expected Monthly Return | 2.848% (~34% annualized) |
| Portfolio Std Dev | 2.236% / month |
| Frontier Solutions | 28 / 28 feasible |
| Constraint Violations | 0 / 28 |
| Stocks Selected | 10 from 31 qualified |
| Backtest Final (MINLP) | $1.0795 |
| Backtest Final (SPY) | $1.2200 |

Top holdings: AVGO (18.9%), XOM (26.1%), WMT (17.1%), WFC (6.7%), JNJ (6.2%)

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Optimization | Pyomo · Bonmin (COIN-OR) · IDAES |
| Data | yfinance · pandas · numpy |
| ML / SHAP | scikit-learn · RandomForestRegressor · shap |
| AI Layer | Anthropic Claude API (claude-sonnet-4) |
| Automation | GitHub Actions · Python cron |
| Dashboard | HTML · Chart.js 4.4 |
| Environment | Google Colab (primary) · Python 3.10+ |

---

## Course Context

OPIM 5641 · Business Decision Modeling · MS Business Analytics & Project Management · University of Connecticut · Spring 2026

The base model extends the Womack MINLP textbook example into a fully generalized, live-data system. Steps 12–14 were added beyond the assignment requirements to demonstrate comparative model evaluation and AI-assisted decision support.

---

*Jonathan Trippett, MD, BCMAS · github.com/JRTrippett/Investment-Project*
