"""
synthesizer.py — Sprint 2 AI Brain
=====================================
Takes the original prompt and a list of search results from parallel
web searches, then uses gpt-4o-mini to synthesize a clean, structured
Markdown research report.
"""

import logging
import os

from openai import OpenAI

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert research analyst. You are given a user's research question
and raw web search results from multiple independent searches conducted in parallel.

Your task is to synthesize these findings into a comprehensive, well-structured Markdown report.

Requirements:
- Use proper Markdown headings (##, ###)
- Include a brief executive summary at the top
- Organize findings by theme, not by search query
- Cite sources where relevant using [Source](url) markdown links
- End with a "Key Takeaways" section with 3–5 bullet points
- Be concise but thorough; aim for 400–800 words
"""


def synthesize(prompt: str, search_results: list[str]) -> str:
    """
    Synthesizes parallel search results into a Markdown report.

    Args:
        prompt: The original user research question.
        search_results: List of text results from each parallel search agent.

    Returns:
        A structured Markdown string containing the final research report.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    combined_results = "\n\n---\n\n".join(
        [f"**Search Result {i + 1}:**\n{r}" for i, r in enumerate(search_results)]
    )

    user_message = (
        f"**Research Question:** {prompt}\n\n"
        f"**Raw Search Results:**\n\n{combined_results}"
    )

    log.info("Synthesizing %d search results into final report...", len(search_results))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.4,
        max_tokens=2048,
    )

    report = response.choices[0].message.content.strip()
    log.info("Synthesis complete — report is %d chars", len(report))
    return report
