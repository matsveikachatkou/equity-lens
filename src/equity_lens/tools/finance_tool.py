from crewai.tools import BaseTool
from typing import Type, Any
from pydantic import BaseModel, Field
import yfinance as yf
import json


class FinanceInput(BaseModel):
    ticker: Any = Field(..., description="Stock ticker symbol e.g. NVDA, AAPL, WISE.L")


class YFinanceTool(BaseTool):
    name: str = "Get Financial Data"
    description: str = (
        "Retrieves real financial data for a stock ticker including market cap, "
        "PE ratio, EV/EBITDA, revenue growth, operating margin, FCF margin, "
        "debt/EBITDA, and dividend yield. For European stocks use exchange suffix: "
        ".L for London, .AS for Amsterdam, .PA for Paris, .DE for Frankfurt, "
        ".MI for Milan. Always use this tool for fundamental financial metrics."
    )
    args_schema: Type[BaseModel] = FinanceInput

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
                    f"{ticker}.DE", f"{ticker}.MI"]

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
            data = {
                "ticker": used_ticker,
                "name": info.get("longName") or info.get("shortName"),
                "exchange": info.get("exchange"),
                "market_cap_usd": info.get("marketCap"),
                "pe_ttm": info.get("trailingPE"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "revenue_growth_yoy": round(info.get("revenueGrowth", 0) * 100, 2) if info.get("revenueGrowth") else None,
                "operating_margin_ttm": round(info.get("operatingMargins", 0) * 100, 2) if info.get("operatingMargins") else None,
                "fcf_margin_ttm": None,
                "net_debt_to_ebitda": None,
                "dividend_yield": round(info.get("dividendYield", 0), 4) if info.get("dividendYield") else None,
                "as_of_date": "May 28, 2026",
                "notes": f"Data from yfinance. Sector: {info.get('sector')}. Industry: {info.get('industry')}."
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