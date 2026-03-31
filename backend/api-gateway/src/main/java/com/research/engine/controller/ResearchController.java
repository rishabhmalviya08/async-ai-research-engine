package com.research.engine.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.research.engine.kafka.KafkaProducerService;
import com.research.engine.model.ResearchJob;
import com.research.engine.repository.ResearchJobRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/v1/research")
@RequiredArgsConstructor
public class ResearchController {

    private final ResearchJobRepository jobRepository;
    private final KafkaProducerService kafkaProducer;
    private final ObjectMapper objectMapper;

    /**
     * POST /api/v1/research
     *
     * Body: {"clientId": "abc-123", "prompt": "Compare AI hardware investments..."}
     *
     * Creates a PENDING job in MongoDB, publishes to Kafka, and returns 202 immediately.
     */
    @PostMapping
    public ResponseEntity<Map<String, String>> submitResearch(@RequestBody Map<String, String> body) {
        String clientId = body.get("clientId");
        String prompt   = body.get("prompt");

        if (clientId == null || clientId.isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "clientId is required"));
        }
        if (prompt == null || prompt.isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "prompt is required"));
        }

        // 1. Create job in MongoDB
        String jobId = UUID.randomUUID().toString();
        ResearchJob job = new ResearchJob();
        job.setId(jobId);
        job.setClientId(clientId);
        job.setPrompt(prompt);
        job.setStatus(ResearchJob.JobStatus.PENDING);
        job.setCreatedAt(Instant.now());
        jobRepository.save(job);
        log.info("Created job jobId={} for clientId={}", jobId, clientId);

        // 2. Publish task to Kafka
        try {
            String kafkaPayload = objectMapper.writeValueAsString(Map.of(
                    "jobId",    jobId,
                    "clientId", clientId,
                    "prompt",   prompt
            ));
            kafkaProducer.publishResearchTask(jobId, kafkaPayload);
        } catch (Exception e) {
            log.error("Failed to serialize Kafka payload for jobId={}", jobId, e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Failed to queue research task"));
        }

        // 3. Return 202 Accepted immediately — HTTP connection closes here
        return ResponseEntity.accepted().body(Map.of(
                "jobId",  jobId,
                "status", "processing"
        ));
    }

    /**
     * GET /api/v1/research/{jobId}
     *
     * Returns the full job document including status and resultText.
     */
    @GetMapping("/{jobId}")
    public ResponseEntity<?> getJob(@PathVariable String jobId) {
        return jobRepository.findById(jobId)
                .<ResponseEntity<?>>map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}
