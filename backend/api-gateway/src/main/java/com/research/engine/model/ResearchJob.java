package com.research.engine.model;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "jobs")
public class ResearchJob {

    @Id
    private String id;

    private String clientId;
    private String prompt;
    private JobStatus status;
    private String resultText;
    private Instant createdAt;
    private Instant completedAt;

    public enum JobStatus {
        PENDING, PROCESSING, COMPLETED, FAILED
    }
}
