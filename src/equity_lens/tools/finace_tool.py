from crewai.tools import BaseTool
from typing import Type, Any
from pydantic import BaseModel, Field
import yfinance as yf
import json


class FinanceInput(BaseModel):
    ticker: Any = Field(..., description="Stock ticker symbol e.g. NVDA, AAPL")


class YFinanceTool(BaseTool):
    name: str = "Get Financial Data"
    description: str = (
        "Retrieves real financial data for a stock ticker including market cap, "
        "PE ratio, EV/EBITDA, revenue growth, operating margin, FCF margin, "
        "debt/EBITDA, and dividend yield. Always use this tool to get "
        "fundamental financial metrics instead of searching the web."
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

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            data = {
                "ticker": ticker,
                "name": info.get("longName") or info.get("shortName"),
                "exchange": info.get("exchange"),
                "market_cap_usd": info.get("marketCap"),
                "pe_ttm": info.get("trailingPE"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "revenue_cagr_3y": None,  # requires historical calculation
                "operating_margin_ttm": round(info.get("operatingMargins", 0) * 100, 2) if info.get("operatingMargins") else None,
                "fcf_margin_ttm": None,  # calculated below
                "net_debt_to_ebitda": None,  # calculated below
                "dividend_yield": round(info.get("dividendYield", 0) * 100, 2) if info.get("dividendYield") else None,
                "as_of_date": "current",
                "notes": f"Data from yfinance. Sector: {info.get('sector')}. Industry: {info.get('industry')}."
            }

            # Calculate FCF margin
            fcf = info.get("freeCashflow")
            revenue = info.get("totalRevenue")
            if fcf and revenue and revenue > 0:
                data["fcf_margin_ttm"] = round((fcf / revenue) * 100, 2)

            # Calculate net debt / EBITDA
            total_debt = info.get("totalDebt", 0)
            cash = info.get("totalCash", 0)
            ebitda = info.get("ebitda")
            if ebitda and ebitda > 0:
                net_debt = (total_debt or 0) - (cash or 0)
                data["net_debt_to_ebitda"] = round(net_debt / ebitda, 2)

            # Revenue CAGR approximation using growth rate
            revenue_growth = info.get("revenueGrowth")
            if revenue_growth:
                data["revenue_cagr_3y"] = round(revenue_growth * 100, 2)

            return json.dumps(data, indent=2)

        except Exception as e:
            return json.dumps({"ticker": ticker, "error": str(e)})