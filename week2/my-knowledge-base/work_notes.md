# Work Notes & Learnings

## Meeting Notes - Jan 2025
- Team decided to migrate from monolith to microservices architecture
- API gateway will use Kong; each service gets its own database
- Target: complete migration by Q3 2025
- My responsibility: user service and authentication module

## Key Decisions
- Adopted FastAPI over Flask for new services (better async support, auto docs)
- Using Redis for caching and session management
- Switched from REST to GraphQL for the frontend BFF layer
- Implemented feature flags using LaunchDarkly

## Lessons Learned
- Always add database indexes on frequently queried columns - reduced query time by 80%
- Use connection pooling (PgBouncer) to handle high concurrent database connections
- Implement circuit breakers for external API calls to prevent cascade failures
- Write integration tests, not just unit tests - caught 3 critical bugs in staging

## Reading List
- "Designing Data-Intensive Applications" by Martin Kleppmann - excellent for system design
- "Building LLM Applications" course on Coursera - good intro to RAG and agents
- "Clean Architecture" by Robert C. Martin - useful patterns for service boundaries
