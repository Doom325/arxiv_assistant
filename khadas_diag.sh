#!/bin/bash
# Diagnostic Script for ArXiv Assistant on Khadas

echo "--- 1. Container Status ---"
sudo docker ps -a --filter "name=arxiv_assistant"

echo -e "\n--- 2. Environment Variables (.env) ---"
cat ~/arxiv_assistant/.env

echo -e "\n--- 3. Mount Status ---"
mount | grep -E "External1|postgres_mount"

echo -e "\n--- 4. Mount Point Content ---"
ls -F ~/arxiv_assistant/postgres_mount/
ls -F ~/arxiv_assistant/postgres_mount/pgdata/ 2>/dev/null || echo "pgdata folder not found inside mount point"

echo -e "\n--- 5. Database Container Logs (Last 20 lines) ---"
sudo docker compose -f ~/arxiv_assistant/docker-compose.yml logs db --tail 20

echo -e "\n--- 6. Backend Container Logs (Last 20 lines) ---"
sudo docker compose -f ~/arxiv_assistant/docker-compose.yml logs backend --tail 20

echo -e "\n--- 7. Disk Space ---"
df -h | grep -E "Filesystem|External1|postgres_mount|root"
