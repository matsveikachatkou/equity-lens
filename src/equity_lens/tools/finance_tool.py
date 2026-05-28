from crewai.tools import BaseTool
from typing import Type, Any
from pydantic import BaseModel, Field
from decimal import Decimal
import yfinance as yf
import json


class FinanceInput(BaseModel):
    ticker: Any = Field(..., description="Stock ticker symbol e.g. NVDA, AAPL, 6857.T, 000660.KS")


class YFinanceTool(BaseTool):
    name: str = "Get Financial Data"
    description: str = (
        "Retrieves real financial data for a stock ticker including market cap in USD, "
        "PE ratio, EV/EBITDA, revenue growth, operating margin, FCF margin, "
        "debt/EBITDA, and dividend yield. Handles all exchanges including US, European "
        "and Asian markets. Always use this tool for fundamental financial metrics."
    )
    args_schema: Type[BaseModel] = FinanceInput

    def _get_usd_rate(self, currency: str) -> float:
        """Fetch live FX rate to USD via yfinance, with hardcoded fallback."""
        if currency == "USD":
            return 1.0
        try:
            fx = yf.Ticker(f"{currency}=X")
            rate = fx.info.get("regularMarketPrice")
            if rate:
                return float(rate)
        except Exception:
            pass
        # Hardcoded fallback rates
        fallback = {
            "EUR": 1.08, "GBP": 1.27, "JPY": 0.0067,
            "KRW": 0.00072, "HKD": 0.128, "TWD": 0.031,
            "SGD": 0.74, "CNY": 0.138,
        }
        return fallback.get(currency, 1.0)

    def _run(self, ticker: Any) -> str:
        if isinstance(ticker, dict):
            ticker = (
                ticker.get("ticker") or
                ticker.get("symbol") or
                ticker.get("description") or
                str(ticker)
            )
        ticker = str(ticker).strip().upper()

        # Try original ticker first, then common exchange suffixes
        attempts = [ticker, f"{ticker}.L", f"{ticker}.AS", f"{ticker}.PA",
                    f"{ticker}.DE", f"{ticker}.MI", f"{ticker}.T",
                    f"{ticker}.KS", f"{ticker}.HK", f"{ticker}.TW",
                    f"{ticker}.SI"]

        info = {}
        used_ticker = ticker
        for t in attempts:
            try:
                stock = yf.Ticker(t)
                i = stock.info
                if i.get("marketCap") or i.get("trailingPE"):
                    info = i
                    used_ticker = t
                    break
            except Exception:
                continue

        if not info:
            return json.dumps({
                "ticker": ticker,
                "error": "No data found — company may be private or ticker incorrect"
            })

        try:
            # Normalize market cap to USD
            currency = info.get("currency", "USD")
            fx_rate = self._get_usd_rate(currency)
            market_cap_local = info.get("marketCap")
            if market_cap_local:
                market_cap_usd = int(Decimal(str(market_cap_local)) * Decimal(str(fx_rate)))
            else:
                market_cap_usd = None

            data = {
                "ticker": used_ticker,
                "name": info.get("longName") or info.get("shortName"),
                "exchange": info.get("exchange"),
                "currency": currency,
                "market_cap_usd": market_cap_usd,
                "pe_ttm": info.get("trailingPE"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "revenue_growth_yoy": round(info.get("revenueGrowth", 0) * 100, 2) if info.get("revenueGrowth") else None,
                "operating_margin_ttm": round(info.get("operatingMargins", 0) * 100, 2) if info.get("operatingMargins") else None,
                "fcf_margin_ttm": None,
                "net_debt_to_ebitda": None,
                "dividend_yield": round(info.get("dividendYield", 0), 4) if info.get("dividendYield") else None,
                "as_of_date": "current",
                "notes": f"Data from yfinance. Currency: {currency}. Sector: {info.get('sector')}. Industry: {info.get('industry')}."
            }

            # FCF margin
            fcf = info.get("freeCashflow")
            revenue = info.get("totalRevenue")
            if fcf and revenue and revenue > 0:
                data["fcf_margin_ttm"] = round((fcf / revenue) * 100, 2)

            # Net debt / EBITDA
            total_debt = info.get("totalDebt", 0)
            cash = info.get("totalCash", 0)
            ebitda = info.get("ebitda")
            if ebitda and ebitda > 0:
                net_debt = (total_debt or 0) - (cash or 0)
                data["net_debt_to_ebitda"] = round(net_debt / ebitda, 2)

            return json.dumps(data, indent=2)

        except Exception as e:
            return json.dumps({"ticker": ticker, "error": str(e)})