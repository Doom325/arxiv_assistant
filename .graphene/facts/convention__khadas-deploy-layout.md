---
category: convention
subject: khadas-deploy-layout
---

Production runs on a Khadas box (ssh khadas@192.168.1.49, key auth works from the dev Mac). /home/khadas/arxiv_assistant is a PLAIN COPY of the repo, not a git checkout, with docker-compose.yml + docker-compose.khadas-ollama.yml (use both `-f` flags). Services: backend, worker, frontend, db (+ grobid, see below).

- backend and worker bind-mount ./backend:/app, so a backend change is: copy the changed files into /home/khadas/arxiv_assistant/backend/... and `docker compose ... restart backend` (and `restart worker`; the worker only loads new code on restart). No image rebuild.
- frontend is a baked Next.js image: copy the files, `docker compose ... build frontend` (about 2 min on the box), then `up -d --no-deps frontend`.
- Safe deploy recipe used for PR #59: (1) confirm the host files' md5 equal the base commit, (2) tar a backup of the files to be replaced in /home/khadas/backup-pre-<change>-<ts>.tgz, (3) `git archive <commit> <files>` locally, scp, extract over the tree, (4) restart/rebuild as above, (5) verify via `docker exec -i arxiv_assistant_backend python -` hitting http://localhost:8000. Use `docker exec -i` when feeding a heredoc.
- PDFs live on the 466G exFAT drive mounted at /app/data (PDF_SAVE_DIR). DB container arxiv_assistant_db: `psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"` from inside the container.
- Open ops problems seen 2026-11-04 (worker logs): the Gemini embedding API returns 403 PERMISSION_DENIED "API key was reported as leaked" (key must be rotated), and the grobid container is not running (host `grobid` unreachable, citation extraction fails). Neither is related to the PDF work.
