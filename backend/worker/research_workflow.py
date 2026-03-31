"""
research_workflow.py — Sprint 2 AI Brain
=========================================
Orchestrates the full scatter-gather research workflow:
  1. Planner  — decomposes prompt into N parallel search queries
  2. Scatter  — runs N searches concurrently with asyncio.gather()
  3. Gather   — synthesizes all results into a Markdown report

Can be run standalone for testing:
    python research_workflow.py

Requires worker/.env with OPENAI_API_KEY and TAVILY_API_KEY.
"""

import asyncio
import logging
import os
import sys
import time

from dotenv import load_dotenv

import planner
import search_agent
import synthesizer

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger(__name__)


async def run_research(prompt: str) -> str:
    """
    Executes the full scatter-gather research workflow.

    Args:
        prompt: The user's complex research question.

    Returns:
        A Markdown-formatted research report as a string.
    """
    log.info("=== Starting research workflow ===")
    log.info("Prompt: %s", prompt)
    start = time.perf_counter()

    # --- Phase 1: Plan ---
    tasks = planner.decompose(prompt)
    log.info("Planner produced %d sub-tasks", len(tasks))

    # --- Phase 2: Scatter (parallel search) ---
    log.info("Scattering %d search agents in parallel...", len(tasks))
    scatter_start = time.perf_counter()
    results = await asyncio.gather(*[search_agent.search(t) for t in tasks])
    scatter_elapsed = time.perf_counter() - scatter_start
    log.info("All searches complete in %.2fs", scatter_elapsed)

    # --- Phase 3: Gather (synthesize) ---
    report = synthesizer.synthesize(prompt, list(results))

    total_elapsed = time.perf_counter() - start
    log.info("=== Research workflow complete in %.2fs ===", total_elapsed)

    return report


# ---------------------------------------------------------------------------
# Standalone test entrypoint (Sprint 2 validation)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_prompt = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Compare Meta and Google's AI hardware investments and strategies in 2024."
    )

    print("\n" + "=" * 60)
    print("Running standalone research workflow test...")
    print(f"Prompt: {test_prompt}")
    print("=" * 60 + "\n")

    report = asyncio.run(run_research(test_prompt))

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(report)
    print("=" * 60 + "\n")
