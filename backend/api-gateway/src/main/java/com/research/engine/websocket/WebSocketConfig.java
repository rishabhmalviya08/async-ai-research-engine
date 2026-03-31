package com.research.engine.websocket;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {

    private final ResearchWebSocketHandler researchWebSocketHandler;

    public WebSocketConfig(ResearchWebSocketHandler researchWebSocketHandler) {
        this.researchWebSocketHandler = researchWebSocketHandler;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry
                .addHandler(researchWebSocketHandler, "/ws/research")
                .setAllowedOrigins("*");
    }
}
