---
description: Deploy arxiv_assistant to the Khadas Edge 2 or run locally on Framework Desktop.
---

# /deploy — Deploy Application

## Pre-flight Checks

1. Verify all tests pass:
   ```bash
   cd backend && make test-unit
   ```

2. Check for uncommitted changes:
   ```bash
   git status
   ```

3. Ask the user which target to deploy to:
   - **Framework Desktop** (local Docker Compose with Ollama)
   - **Khadas Production** (rsync + Docker Compose to 192.168.1.49)
   - **Khadas Staging** (separate ports/DB at ~/arxiv_assistant_staging/)

## Framework Desktop

4. Verify Ollama is running and models are available:
   ```bash
   curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; tags=json.load(sys.stdin); print([m['name'] for m in tags.get('models',[])])"
   ```

5. Start the stack:
   ```bash
   EXTERNAL_DRIVE_PATH=/mnt/external GEMINI_API_KEY=${GEMINI_API_KEY} docker compose \
     -f docker-compose.yml -f docker-compose.framework.yml up -d
   ```

## Khadas Production

4. Confirm with user before deploying to production.

5. Run the deploy script:
   ```bash
   ./deploy.sh
   ```

## Khadas Staging

4. Run the staging deploy script:
   ```bash
   ./deploy-staging.sh
   ```

## Post-deploy

6. Verify the backend health check:
   ```bash
   curl -s http://localhost:8000/ | python3 -c "import sys,json; print(json.load(sys.stdin))"
   ```

7. Verify the frontend is serving:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/
   ```
