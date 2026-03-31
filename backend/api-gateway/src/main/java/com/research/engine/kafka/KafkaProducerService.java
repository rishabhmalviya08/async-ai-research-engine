package com.research.engine.kafka;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class KafkaProducerService {

    private static final String RESEARCH_TASKS_TOPIC = "research-tasks";

    private final KafkaTemplate<String, String> kafkaTemplate;

    /**
     * Publishes a JSON-serialized task message to the research-tasks Kafka topic.
     *
     * @param jobId    unique job identifier (used as Kafka message key)
     * @param jsonBody JSON string produced by the caller (includes jobId, clientId, prompt)
     */
    public void publishResearchTask(String jobId, String jsonBody) {
        kafkaTemplate.send(RESEARCH_TASKS_TOPIC, jobId, jsonBody);
        log.info("Published research task jobId={} to topic={}", jobId, RESEARCH_TASKS_TOPIC);
    }
}
