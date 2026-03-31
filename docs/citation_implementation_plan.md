# Plan: Fix Citation Extraction in Daily Ingestion

The `production_worker` is responsible for extracting citations from newly ingested papers. Currently, it is failing because it lacks the necessary environment variables to connect to Gemini, causing it to fall back to a non-existent local Ollama instance.

## Proposed Changes

### [Component] Infrastructure

#### [MODIFY] [docker-compose.yml](file:///Users/sumanthgottipati/git/arxiv_assistant/docker-compose.yml)
- Add `AI_PROVIDER` and `GEMINI_API_KEY` to the [worker](file:///Users/sumanthgottipati/git/arxiv_assistant/backend/production_worker.py#420-638) service environment.
- Add `RESEND_API_KEY`, `EMAIL_SENDER`, and `EMAIL_RECIPIENTS` to the [worker](file:///Users/sumanthgottipati/git/arxiv_assistant/backend/production_worker.py#420-638) service environment for consistency.
- Add `extra_hosts` to the [worker](file:///Users/sumanthgottipati/git/arxiv_assistant/backend/production_worker.py#420-638) service to allow `host.docker.internal` resolution if needed.

## Verification Plan

### Automated Verification
1.  Deploy the changes using [deploy.sh](file:///Users/sumanthgottipati/git/arxiv_assistant/deploy.sh).
2.  Tail the logs of the `arxiv_assistant_worker` container.
3.  Observe the logs to ensure the worker successfully connects to Gemini and proceeds past the embedding/citation steps for pending papers.
4.  Query the database to confirm [citations](file:///Users/sumanthgottipati/git/arxiv_assistant/backend/services/llm_service.py#282-306) is no longer `[]` or `None` for recent papers.

### Manual Verification
1.  Wait for the 15-minute poll to ingest new papers.
2.  Verify that the paper detail page shows extracted citations for the new papers.
