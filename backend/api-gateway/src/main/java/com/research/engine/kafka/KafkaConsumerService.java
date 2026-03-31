package com.research.engine.kafka;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.research.engine.websocket.ResearchWebSocketHandler;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class KafkaConsumerService {

    private final ResearchWebSocketHandler webSocketHandler;
    private final ObjectMapper objectMapper;

    /**
     * Consumes completion events from the research-results topic.
     * Parses the JSON payload and pushes a JOB_FINISHED notification
     * to the correct client via WebSocket.
     *
     * Expected payload: {"jobId": "...", "clientId": "...", "status": "COMPLETED|FAILED"}
     */
    @KafkaListener(topics = "research-results", groupId = "api-gateway-group")
    public void onResearchResult(String message) {
        log.info("Consumed message from research-results: {}", message);
        try {
            @SuppressWarnings("unchecked")
            Map<String, String> payload = objectMapper.readValue(message, Map.class);

            String jobId    = payload.get("jobId");
            String clientId = payload.get("clientId");
            String status   = payload.get("status");

            if (clientId == null || jobId == null) {
                log.error("Invalid result message — missing jobId or clientId: {}", message);
                return;
            }

            Map<String, String> wsPayload = Map.of(
                    "event",  "JOB_FINISHED",
                    "jobId",  jobId,
                    "status", status != null ? status : "UNKNOWN"
            );
            webSocketHandler.sendToClient(clientId, wsPayload);

        } catch (Exception e) {
            log.error("Failed to process research-results message: {}", message, e);
        }
    }
}
