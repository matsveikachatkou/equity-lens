from crewai.tools import BaseTool
from typing import Type, Any
from pydantic import BaseModel, Field
import os
import requests


class SearchInput(BaseModel):
    search_query: Any = Field(
        ..., description="Search query to use to search the internet"
    )


class RobustSearchTool(BaseTool):
    name: str = "Search the internet with Serper"
    description: str = (
        "A tool that can be used to search the internet with a search_query. "
        "Supports different search types: 'search' (default), 'news'"
    )
    args_schema: Type[BaseModel] = SearchInput

    def _run(self, search_query: Any) -> str:
        # Extract string from whatever the LLM passes
        if isinstance(search_query, dict):
            search_query = (
                search_query.get("search_query") or
                search_query.get("query") or
                search_query.get("description") or
                str(search_query)
            )
        elif not isinstance(search_query, str):
            search_query = str(search_query)

        api_key = os.getenv("SERPER_API_KEY")
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        payload = {"q": search_query, "num": 10}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = []
            for item in data.get("organic", []):
                results.append(f"Title: {item.get('title')}\nLink: {item.get('link')}\nSnippet: {item.get('snippet')}\n")
            return "\n".join(results) if results else str(data)
        except requests.exceptions.RequestException as e:
            return f'{{"error": "{str(e)}"}}'