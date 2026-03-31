"""
search_agent.py — Sprint 2 AI Brain
======================================
Async web search agent using the Tavily API via LangChain.
Each call performs a focused web search and returns a text summary
of the top results for consumption by the synthesizer.
"""

import asyncio
import logging
import os

from langchain_community.tools.tavily_search import TavilySearchResults

log = logging.getLogger(__name__)


async def search(query: str, max_results: int = 5) -> str:
    """
    Performs an async web search for the given query using Tavily.

    Args:
        query: The focused search query string.
        max_results: Number of top results to retrieve.

    Returns:
        A concatenated string of result titles and content snippets.
    """
    log.info("Searching: '%s'", query)

    tool = TavilySearchResults(
        api_key=os.getenv("TAVILY_API_KEY"),
        max_results=max_results,
    )

    # Tavily's LangChain tool is synchronous; run it in a thread pool
    # so it doesn't block the event loop when called with asyncio.gather()
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, tool.run, query)

    if isinstance(results, list):
        snippets = []
        for r in results:
            title   = r.get("title", "No title")
            content = r.get("content", "")
            url     = r.get("url", "")
            snippets.append(f"### {title}\nSource: {url}\n{content}")
        combined = "\n\n".join(snippets)
    else:
        combined = str(results)

    log.info("Search complete for '%s' — %d chars retrieved", query, len(combined))
    return combined
