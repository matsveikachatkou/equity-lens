# Equity Lens

An AI-powered multi-agent investment research pipeline built with CrewAI. Given an investment universe and strategy preference, Equity Lens autonomously discovers publicly traded candidates, screens fundamentals, scores and ranks companies, and delivers a structured investment recommendation.

## Architecture

The pipeline runs six specialist agents sequentially, each with a defined scope and toolset:

```
Universe Mapping → Candidate Discovery → Fundamental Screening → Research → Scoring → Recommendation
```

| Agent | Role | Tools |
|---|---|---|
| `universe_mapper` | Translates input universe into precise search vocabulary | Search, WebRAG |
| `equity_scout` | Discovers 4-6 publicly traded candidates with correct exchange tickers | Search, WebRAG, Scraper |
| `fundamental_screener` | Collects real financial metrics via yFinance | Search, WebRAG, Scraper, yFinance |
| `market_analyst` | Produces per-company research notes | Search, WebRAG, Scraper |
| `valuation_scorer` | Computes rank-based composite scores | GPT-4o |
| `investment_advisor` | Selects best opportunity and writes structured report | GPT-4o |

## Key Design Decisions

**Sequential process over hierarchical** — deterministic execution with clear artifact handoff between stages. Each agent receives structured output from the previous stage via explicit context dependencies.

**Real financial data via yFinance** — the `fundamental_screener` uses a custom `YFinanceTool` to pull live market data (PE, EV/EBITDA, margins, FCF, net debt) directly from Yahoo Finance. Market caps are normalized to USD using live FX rates. European and Asian tickers are handled automatically with exchange suffixes (`.L`, `.AS`, `.PA`, `.DE`, `.T`, `.KS`, `.HK`, `.TW`).

**Rank-based scoring** — relative valuation using PE, EV/EBITDA, margins, and revenue growth. Robust to missing data via neutral rank imputation. Configurable weighting via `--strategy` flag.

**Date injection** — `{current_date}` flows through every agent and task prompt, enforcing data freshness and preventing stale financial data from prior years entering the pipeline.

**Tradability enforcement** — major exchange listing and market cap floor verified at discovery stage. Private companies, OTC-only listings, and ADRs for non-US stocks are explicitly excluded. Primary exchange tickers enforced for all markets.

**Geography auto-expansion** — when fewer than 4 companies meet the geography criteria, the pipeline automatically expands to global markets for comparison while prioritizing the specified geography in the final selection.

**Robust tool wrappers** — custom wrappers around SerperDev handle edge cases where the LLM passes malformed tool arguments, preventing pipeline failures.

**Artifact chain** — numbered outputs (`01_` through `06_`) written to `output/` for full auditability and comparison across runs.

## Outputs

Each run produces six artifacts in `output/`:

```
01_universe_mapping.yaml   — search vocabulary and scope boundaries
02_candidates.json         — discovered companies with exchange and market cap
03_fundamentals.json       — screened financial metrics with data lineage
04_research.md             — per-company research notes
05_scores.json             — composite scores with weighting breakdown
06_recommendation.md       — final investment recommendation
```

## Setup

**1. Clone and install dependencies:**

```bash
git clone https://github.com/matsveikachatkou/equity-lens.git
cd equity-lens
uv sync
```

> **Intel Mac users:** The project is configured for Intel Mac (x86_64) in `pyproject.toml`. If you are on Apple Silicon (M1/M2/M3) or Linux, remove the `[tool.uv]` section from `pyproject.toml` before running `uv sync`.

**2. Configure environment variables:**

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```
OPENAI_API_KEY=your_openai_api_key
SERPER_API_KEY=your_serper_api_key
```

## Usage

```bash
# Default — Technology, global, balanced strategy, 12-month horizon
uv run equity_lens

# Semiconductors, US market, growth strategy
uv run equity_lens --universe "Semiconductors" --geography "US" --strategy growth

# European fintech, balanced strategy
uv run equity_lens --universe "Fintech" --geography "Europe" --strategy balanced

# Asian semiconductors, growth strategy
uv run equity_lens --universe "Semiconductors" --geography "Asia" --strategy growth

# Global cybersecurity, growth strategy
uv run equity_lens --universe "Cybersecurity" --geography "global" --strategy growth

# Large cap only (min $10B market cap)
uv run equity_lens --universe "Cloud Computing" --min-size 10000000000

# All options
uv run equity_lens --universe "AI Infrastructure" --geography "US" --strategy growth --horizon 12 --min-size 2000000000
```

## CLI Reference

| Argument | Default | Description |
|---|---|---|
| `--universe` | Technology | Investment universe to research |
| `--geography` | global | Geographic focus: global, US, Europe, Asia |
| `--strategy` | balanced | Scoring weights: value, growth, balanced |
| `--horizon` | 12 | Holding period in months |
| `--min-size` | 2000000000 | Minimum market cap in USD |
| `--date` | today | Override date for testing |

## Tested Universes

| Universe | Geography | Strategy | Selected | Rationale |
|---|---|---|---|---|
| Semiconductors | US | growth | NVDA | 85.2% YoY revenue growth, 65.6% operating margin, AI chip dominance |
| Semiconductors | Asia | growth | TSM | Leading foundry, NVIDIA partnership, 35% revenue growth |
| Fintech | Europe | balanced | Adyen (ADYEN.AS) | 49.5% operating margin, strong payments infrastructure |
| Healthcare Technology | Europe | value | Smith & Nephew (SNN.L) | Reasonable P/E 20.8x, consistent revenue growth, RISE strategy |
| Cybersecurity | global | growth | CrowdStrike (CRWD) | AI-native Falcon platform, 23.3% revenue growth, cloud-native edge |
| Electric Vehicles | global | growth | Tesla (TSLA) | Superior charging network, production expansion, autonomous driving |

## Requirements

- Python 3.11 (Intel Mac) or 3.11–3.12 (Apple Silicon / Linux)
- OpenAI API key
- Serper API key

## Limitations

- `YFinanceTool` `revenue_growth_yoy` reflects TTM YoY growth, not a true 3-year CAGR
- European and Asian tickers depend on yfinance coverage — some smaller companies may not be available
- For production use, replace web scraping in the research stage with a dedicated financial data API (e.g. Polygon.io, Alpha Vantage)
- Pipeline cost: approximately $0.30–0.80 per run depending on universe size and geography