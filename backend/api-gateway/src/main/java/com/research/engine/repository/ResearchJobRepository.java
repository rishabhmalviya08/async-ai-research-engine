package com.research.engine.repository;

import com.research.engine.model.ResearchJob;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ResearchJobRepository extends MongoRepository<ResearchJob, String> {
}
