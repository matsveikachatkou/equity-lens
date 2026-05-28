from pydantic import BaseModel, Field, RootModel
from typing import List, Optional


class SectorMapping(BaseModel):
    core_terms: List[str] = Field(description="6-12 precise primary search terms")
    adjacent_terms: List[str] = Field(description="4-8 adjacent/synonym terms")
    scope_note: str = Field(description="One-line note on what is in vs out")
    pitfalls: List[str] = Field(description="3-8 common mislabels to avoid")


class EquityCandidate(BaseModel):
    ticker: str = Field(description="Exchange ticker in UPPERCASE, e.g. AAPL")
    name: str
    exchange: Optional[str] = None
    country: Optional[str] = None
    market_cap_usd: Optional[float] = None
    match_reason: Optional[str] = Field(None, description="Why this company fits the universe, max 140 chars")


class FundamentalMetrics(BaseModel):
    ticker: str
    name: str
    market_cap_usd: Optional[float] = None
    pe_ttm: Optional[float] = None
    ev_ebitda: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    operating_margin_ttm: Optional[float] = None
    fcf_margin_ttm: Optional[float] = None
    net_debt_to_ebitda: Optional[float] = None
    dividend_yield: Optional[float] = None
    as_of_date: Optional[str] = Field(None, description="Date of most recent data point")
    notes: Optional[str] = None
    

class ScoredEquity(BaseModel):
    ticker: str
    name: str
    valuation_score: Optional[float] = Field(None, description="Higher is better (cheaper relative valuation)")
    quality_score: Optional[float] = Field(None, description="Higher margins, lower leverage")
    growth_score: Optional[float] = Field(None, description="Higher revenue CAGR")
    composite_score: Optional[float] = Field(None, description="Weighted composite based on strategy")
    scoring_note: Optional[str] = Field(None, description="Explanation of score drivers and any NA handling")


class NewsItem(BaseModel):
    ticker: str
    headline: str
    url: Optional[str] = None
    sentiment: Optional[str] = Field(None, description="positive / neutral / negative")
    materiality_note: Optional[str] = Field(None, description="Why this item matters for the thesis")


class InvestmentPick(BaseModel):
    ticker: str
    name: str
    exchange: str
    thesis: str = Field(description="80-140 word investment thesis covering why now and edge vs peers")
    key_drivers: List[str] = Field(description="3-5 short imperative bullets")
    red_flags: List[str] = Field(description="2-3 short risk bullets")
    one_year_view: Optional[str] = Field(None, description="Forward looking qualitative view")


class InvestmentReport(BaseModel):
    chosen: InvestmentPick
    rejected: List[dict] = Field(description="List of rejected tickers with reason")
    key_risks: List[str] = Field(description="Top 2-3 risks to monitor")


# RootModel wrappers for CrewAI list outputs
class CandidateList(RootModel[List[EquityCandidate]]):
    pass


class MetricsList(RootModel[List[FundamentalMetrics]]):
    pass


class ScoredList(RootModel[List[ScoredEquity]]):
    pass


class NewsItemList(RootModel[List[NewsItem]]):
    pass