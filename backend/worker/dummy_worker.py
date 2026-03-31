"""
Sprint 1 — Dummy Python Worker
================================
Simulates AI processing without any LLM calls.
- Polls the Kafka 'research-tasks' topic
- Sleeps 10 seconds to mimic processing time
- Updates MongoDB job status to COMPLETED
- Publishes a completion event to 'research-results'

Run: python dummy_worker.py
"""

import json
import time
import os
import logging
from datetime import datetime, timezone

from kafka import KafkaConsumer, KafkaProducer
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MONGO_URI       = os.getenv("MONGO_URI", "mongodb://localhost:27017/research_engine")
TASKS_TOPIC     = "research-tasks"
RESULTS_TOPIC   = "research-results"


def main():
    log.info("Connecting to Kafka at %s ...", KAFKA_BOOTSTRAP)
    consumer = KafkaConsumer(
        TASKS_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id="dummy-worker-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    log.info("Connecting to MongoDB at %s ...", MONGO_URI)
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client.get_default_database()
    jobs = db["jobs"]

    log.info("Dummy worker ready — waiting for tasks on '%s'...", TASKS_TOPIC)

    for message in consumer:
        task = message.value
        job_id    = task.get("jobId")
        client_id = task.get("clientId")
        prompt    = task.get("prompt", "")

        log.info("Picked up job: jobId=%s  clientId=%s  prompt='%s'", job_id, client_id, prompt)

        # 1. Mark as PROCESSING
        jobs.update_one({"_id": job_id}, {"$set": {"status": "PROCESSING"}})
        log.info("jobId=%s → PROCESSING", job_id)

        # 2. Simulate AI work
        log.info("Sleeping 10 seconds to simulate AI processing...")
        time.sleep(10)

        # 3. Write dummy result and mark COMPLETED
        dummy_result = (
            f"## Dummy Research Report\n\n"
            f"**Prompt:** {prompt}\n\n"
            f"This is a placeholder result produced by the dummy worker in Sprint 1.\n"
            f"Replace this with the real AI workflow in Sprint 2.\n"
        )
        jobs.update_one(
            {"_id": job_id},
            {"$set": {
                "status": "COMPLETED",
                "resultText": dummy_result,
                "completedAt": datetime.now(timezone.utc).isoformat(),
            }}
        )
        log.info("jobId=%s → COMPLETED", job_id)

        # 4. Publish result event
        result_event = {"jobId": job_id, "clientId": client_id, "status": "COMPLETED"}
        producer.send(RESULTS_TOPIC, value=result_event)
        producer.flush()
        log.info("Published completion event for jobId=%s to '%s'", job_id, RESULTS_TOPIC)


if __name__ == "__main__":
    main()
