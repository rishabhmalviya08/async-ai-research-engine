# async-ai-research-engine
Reducing AI latency by transforming sequential LLM operations into asynchronous, parallel multi-agent workflows.

> A scatter-gather AI backend architecture that accelerates complex LLM workflows by decomposing and executing agentic tasks in parallel, eliminating HTTP timeouts.

## ⚠️ The Problem: Sequential Latency & HTTP Timeouts

As Large Language Models (LLMs) move from simple chat bots to complex, multi-step agentic workflows (like deep web research or codebase analysis), a major architectural bottleneck emerges:

1. **Sequential Latency:** Single AI agents process complex tasks sequentially. If an agent has to search for Data A, read it, then search for Data B, read it, and finally search for Data C, the accumulated latency results in massive wait times.
2. **The HTTP Timeout Issue:** Because standard HTTP requests typically time out after 30 to 60 seconds, users waiting for these sequential agents to finish are frequently met with `504 Gateway Timeout` errors, resulting in broken connections and lost work.

## 💡 The Solution: Parallel Agents + Async Architecture

This project solves the AI latency and timeout problem by implementing a **Scatter-Gather (Map-Reduce) pattern** over an **Asynchronous Event-Driven Architecture**.

Instead of relying on a single sequential agent over a synchronous HTTP connection, this system:
1. Instantly acknowledges the user's request to prevent timeouts.
2. Uses a "Planner" agent to decompose the complex task into smaller, isolated sub-tasks.
3. Spawns multiple, lightweight worker agents to execute these sub-tasks **in parallel** in the background.
4. Synthesizes the parallel findings and pushes the final result back to the client in real-time via **WebSockets**.

## 🛠️ Tech Stack

* **API Gateway & WebSocket Server:** Java, Spring Boot
* **AI Worker Service:** Python, `asyncio`, LangGraph / LangChain
* **Message Broker:** Apache Kafka
* **State Management:** MongoDB
* **LLM & Tooling:** OpenAI API, Tavily Search API

## 🏗️ System Architecture Flow

1. **Ingestion:** Client connects via WebSocket and submits a complex query via a standard HTTP POST request.
2. **Immediate Acknowledgment:** The Spring Boot gateway saves a `PENDING` job to MongoDB, publishes the job payload to a Kafka topic, and instantly returns a `202 Accepted` response. *The HTTP connection closes safely before any timeout can occur.*
3. **Decomposition (Scatter):** The Python background worker consumes the Kafka message. The Planner LLM breaks the prompt into multiple independent search tasks.
4. **Parallel Execution:** The Python worker uses `asyncio` to execute the independent AI agents concurrently, saving massive amounts of time.
5. **Synthesis (Gather):** A Synthesizer LLM merges the concurrent findings into a single cohesive report and updates MongoDB to `COMPLETED`.
6. **Real-Time Delivery:** Python publishes a completion event back to Kafka. Spring Boot consumes this event and pushes the final JSON result down the active WebSocket connection to the original client.
