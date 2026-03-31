package com.research.engine.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Manages WebSocket sessions keyed by clientId.
 *
 * Protocol:
 *   1. Client connects to ws://localhost:8080/ws/research
 *   2. Client sends {"clientId": "abc-123"} as the FIRST message to register.
 *   3. Server stores clientId → session in memory.
 *   4. When a job finishes, KafkaConsumerService calls sendToClient() to push
 *      {"event":"JOB_FINISHED","jobId":"..."} down the open socket.
 */
@Slf4j
@Component
public class ResearchWebSocketHandler extends TextWebSocketHandler {

    private final Map<String, WebSocketSession> sessions = new ConcurrentHashMap<>();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        log.info("WebSocket connection opened — sessionId={}", session.getId());
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String payload = message.getPayload();
        log.debug("Received WS message: {}", payload);

        try {
            @SuppressWarnings("unchecked")
            Map<String, String> data = objectMapper.readValue(payload, Map.class);
            String clientId = data.get("clientId");

            if (clientId != null && !clientId.isBlank()) {
                sessions.put(clientId, session);
                log.info("Registered clientId={} with sessionId={}", clientId, session.getId());
                session.sendMessage(new TextMessage(
                        objectMapper.writeValueAsString(Map.of("event", "REGISTERED", "clientId", clientId))
                ));
            } else {
                log.warn("Message missing 'clientId' field: {}", payload);
            }
        } catch (Exception e) {
            log.error("Failed to parse WS message: {}", payload, e);
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        sessions.entrySet().removeIf(entry -> entry.getValue().getId().equals(session.getId()));
        log.info("WebSocket connection closed — sessionId={} status={}", session.getId(), status);
    }

    /**
     * Called by KafkaConsumerService to push a notification to a connected client.
     */
    public void sendToClient(String clientId, Object payload) {
        WebSocketSession session = sessions.get(clientId);
        if (session == null || !session.isOpen()) {
            log.warn("No open WebSocket session for clientId={}. Message not delivered.", clientId);
            return;
        }
        try {
            String json = objectMapper.writeValueAsString(payload);
            session.sendMessage(new TextMessage(json));
            log.info("Pushed WS message to clientId={}: {}", clientId, json);
        } catch (IOException e) {
            log.error("Failed to send WS message to clientId={}", clientId, e);
        }
    }

    public int getActiveSessionCount() {
        return sessions.size();
    }
}
