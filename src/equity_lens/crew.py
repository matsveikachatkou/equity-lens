from crewai import Agent, Crew, Process, Task, LLM
from crewai.memory.short_term.short_term_memory import ShortTermMemory
from crewai.memory.long_term.long_term_memory import LongTermMemory
from crewai.memory.entity.entity_memory import EntityMemory
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import WebsiteSearchTool, ScrapeWebsiteTool, SerperDevTool
from .tools.finance_tool import YFinanceTool
from .schemas import CandidateList, MetricsList, ScoredList


search_tool = SerperDevTool()
web_rag = WebsiteSearchTool()
scraper = ScrapeWebsiteTool()
finance_tool = YFinanceTool()

default_llm = LLM(model="gpt-4o-mini")
function_llm = LLM(model="gpt-4o-mini")
advisor_llm = LLM(model="gpt-4o")

EMBEDDER_CONFIG = {
    "provider": "openai",
    "config": {
        "model": "text-embedding-3-small",
    },
}

@CrewBase
class EquityLens:
    """Equity Lens — multi-agent investment research pipeline"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def universe_mapper(self) -> Agent:
        return Agent(
            config=self.agents_config["universe_mapper"],
            verbose=True,
            tools=[search_tool, web_rag],
            llm=default_llm,
            function_calling_llm=function_llm,
        )

    @agent
    def equity_scout(self) -> Agent:
        return Agent(
            config=self.agents_config["equity_scout"],
            verbose=True,
            tools=[search_tool, web_rag, scraper],
            llm=default_llm,
            function_calling_llm=function_llm,
        )

    @agent
    def fundamental_screener(self) -> Agent:
        return Agent(
            config=self.agents_config["fundamental_screener"],
            verbose=True,
            tools=[search_tool, finance_tool, web_rag, scraper],
            llm=default_llm,
            function_calling_llm=function_llm,
        )

    @agent
    def market_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["market_analyst"],
            verbose=True,
            tools=[search_tool, web_rag, scraper],
            llm=default_llm,
            function_calling_llm=function_llm,
        )

    @agent
    def valuation_scorer(self) -> Agent:
        return Agent(
            config=self.agents_config["valuation_scorer"],
            verbose=True,
            tools=[],
            llm=default_llm,
            function_calling_llm=function_llm,
        )

    @agent
    def investment_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_advisor"],
            verbose=True,
            tools=[],
            llm=advisor_llm,
            function_calling_llm=advisor_llm,
        )

    @task
    def map_universe(self) -> Task:
        return Task(
            config=self.tasks_config["map_universe"],
        )

    @task
    def discover_candidates(self) -> Task:
        return Task(
            config=self.tasks_config["discover_candidates"],
            output_json=CandidateList,
        )

    @task
    def screen_fundamentals(self) -> Task:
        return Task(
            config=self.tasks_config["screen_fundamentals"],
            output_json=MetricsList,
        )

    @task
    def research_candidates(self) -> Task:
        return Task(
            config=self.tasks_config["research_candidates"],
        )

    @task
    def score_and_rank(self) -> Task:
        return Task(
            config=self.tasks_config["score_and_rank"],
            output_json=ScoredList,
        )

    @task
    def compile_recommendation(self) -> Task:
        return Task(
            config=self.tasks_config["compile_recommendation"],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.universe_mapper(),
                self.equity_scout(),
                self.fundamental_screener(),
                self.market_analyst(),
                self.valuation_scorer(),
                self.investment_advisor(),
            ],
            tasks=[
                self.map_universe(),
                self.discover_candidates(),
                self.screen_fundamentals(),
                self.research_candidates(),
                self.score_and_rank(),
                self.compile_recommendation(),
            ],
            process=Process.sequential,
            verbose=True,
            planning=False,
            memory=True,
            embedder=EMBEDDER_CONFIG,
            short_term_memory=ShortTermMemory(
                crew=None,
                embedder_config=EMBEDDER_CONFIG,
            ),
            long_term_memory=LongTermMemory(),
            entity_memory=EntityMemory(
                crew=None,
                embedder_config=EMBEDDER_CONFIG,
            ),
        )