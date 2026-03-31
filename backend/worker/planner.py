"""
planner.py — Sprint 2 AI Brain
================================
Uses gpt-4o-mini to decompose a complex research prompt into
2–4 focused, independent search queries.
"""

import json
import os
import logging

from openai import OpenAI

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert AI Research Planner orchestrating a parallel multi-agent search system. 
Your job is to decompose a complex user request into a list of highly focused, independent search queries. 

RULES:
1. DECOMPOSE BY ENTITY: If the prompt asks to compare multiple entities (e.g., companies, frameworks, people), create a separate, standalone query for EACH entity. Do not group them.
2. ONLY GATHER DATA: Your queries must be strictly for searching/gathering information. 
3. NO FORMATTING TASKS: Do NOT create tasks for "synthesizing", "writing", "comparing", or "formatting tables". The final synthesis will be handled by a different system. 
4. DYNAMIC COUNT: Create as many parallel queries as necessary to fully cover the original prompt.

Return ONLY a valid JSON array of strings. No explanation, no markdown, just the JSON array.

Example output:
["Query 1 here", "Query 2 here", "Query 3 here"]
"""


def decompose(prompt: str) -> list[str]:
    """
    Decomposes a high-level prompt into a list of parallel search queries.

    Args:
        prompt: The user's complex research question.

    Returns:
        A list of 2–4 focused search query strings.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    log.info("Planning: decomposing prompt into sub-tasks...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Research question: {prompt}"},
        ],
        temperature=0.3,
        max_tokens=512,
    )

    raw = response.choices[0].message.content.strip()
    log.debug("Planner raw response: %s", raw)

    tasks = json.loads(raw)
    if not isinstance(tasks, list) or len(tasks) == 0:
        raise ValueError(f"Planner returned unexpected format: {raw}")

    log.info("Planner produced %d sub-tasks: %s", len(tasks), tasks)
    return tasks
