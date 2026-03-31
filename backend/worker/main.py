"""
main.py — Sprint 3: Full Integration
=======================================
Production Kafka consumer that wires the AI research workflow
to the message bus:

  research-tasks (consumed)
       ↓
  [MongoDB: PROCESSING]
       ↓
  run_research() — parallel scatter-gather AI workflow
       ↓
  [MongoDB: COMPLETED / FAILED]
       ↓
  research-results (published)
       ↓
  Spring Boot WebSocket push to client

Run:
    cd worker
    cp .env.example .env   # add your API keys
    pip install -r requirements.txt
    python main.py
"""

import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from kafka import KafkaConsumer, KafkaProducer
from pymongo import MongoClient

import research_workflow

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MONGO_URI       = os.getenv("MONGO_URI", "mongodb://localhost:27017/research_engine")
TASKS_TOPIC     = "research-tasks"
RESULTS_TOPIC   = "research-results"


def process_task(task: dict, jobs_collection, producer: KafkaProducer):
    """Handles a single research task end-to-end."""
    job_id    = task.get("jobId")
    client_id = task.get("clientId")
    prompt    = task.get("prompt", "")

    log.info("Processing jobId=%s  clientId=%s", job_id, client_id)

    # --- 1. Mark PROCESSING ---
    jobs_collection.update_one(
        {"_id": job_id},
        {"$set": {"status": "PROCESSING"}}
    )

    try:
        # --- 2. Run AI Workflow ---
        markdown_report = asyncio.run(research_workflow.run_research(prompt))

        # --- 3. Persist COMPLETED result ---
        jobs_collection.update_one(
            {"_id": job_id},
            {"$set": {
                "status": "COMPLETED",
                "resultText": markdown_report,
                "completedAt": datetime.now(timezone.utc).isoformat(),
            }}
        )
        log.info("jobId=%s → COMPLETED", job_id)

        # --- 4. Publish success event ---
        _publish_result(producer, job_id, client_id, "COMPLETED")

    except Exception as e:
        log.exception("jobId=%s failed: %s", job_id, e)
        jobs_collection.update_one(
            {"_id": job_id},
            {"$set": {
                "status": "FAILED",
                "resultText": f"Research failed: {str(e)}",
                "completedAt": datetime.now(timezone.utc).isoformat(),
            }}
        )
        _publish_result(producer, job_id, client_id, "FAILED")


def _publish_result(producer: KafkaProducer, job_id: str, client_id: str, status: str):
    """Publishes a completion/failure event to the research-results topic."""
    event = {"jobId": job_id, "clientId": client_id, "status": status}
    producer.send(RESULTS_TOPIC, value=event)
    producer.flush()
    log.info("Published %s event for jobId=%s to '%s'", status, job_id, RESULTS_TOPIC)


def main():
    log.info("=== AI Research Worker starting (Sprint 3) ===")
    log.info("Kafka: %s | MongoDB: %s", KAFKA_BOOTSTRAP, MONGO_URI)

    # Graceful shutdown
    running = True
    def _shutdown(sig, frame):
        nonlocal running
        log.info("Received signal %s — shutting down...", sig)
        running = False
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    consumer = KafkaConsumer(
        TASKS_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id="ai-worker-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        consumer_timeout_ms=1000,   # allows checking `running` flag in loop
    )
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client.get_default_database()
    jobs = db["jobs"]

    log.info("Worker ready — listening on '%s'...", TASKS_TOPIC)

    while running:
        for message in consumer:
            if not running:
                break
            task = message.value
            process_task(task, jobs, producer)

    log.info("Worker shut down cleanly.")
    consumer.close()
    producer.close()
    mongo_client.close()


if __name__ == "__main__":
    main()
