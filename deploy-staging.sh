#!/bin/bash
set -e

# ============================================================================
# Staging Deployment to Khadas Edge 2
# Deploys to ~/arxiv_assistant_staging/ alongside production ~/arxiv_assistant/
# Uses docker-compose.test.yml (different container names, ports, DB)
# ============================================================================

# Configuration (override with environment variables)
KHADAS_IP="${KHADAS_IP:-192.168.1.49}"
REMOTE_USER="${KHADAS_USER:-khadas}"
export SSHPASS="${KHADAS_PASSWORD:-khadas}"
PROJECT_DIR="/Users/sumanthgottipati/git/arxiv_assistant"
REMOTE_STAGING_DIR="~/arxiv_assistant_staging"

echo "🧪 Starting STAGING Deployment to Khadas Edge 2 ($KHADAS_IP)..."
echo "   Target: $REMOTE_STAGING_DIR (separate from production)"
echo ""

# 0. Get Gemini API key from local backend/.env
GEMINI_KEY=$(grep GEMINI_API_KEY "$PROJECT_DIR/backend/.env" | cut -d'=' -f2 | tr -d '"' || echo "")
RESEND_KEY=$(grep RESEND_API_KEY "$PROJECT_DIR/backend/.env" | cut -d'=' -f2 | tr -d '"' || echo "")

# 1. Sync files using rsync
echo "📂 Syncing files to Khadas staging directory..."
export RSYNC_RSH="sshpass -e ssh -o StrictHostKeyChecking=no -T"
rsync -avzi --progress \
    --exclude '.git' \
    --exclude 'node_modules' \
    --exclude '__pycache__' \
    --exclude '.env' \
    --exclude 'PDFs' \
    --exclude 'data' \
    --exclude 'venv' \
    --exclude '.next' \
    "$PROJECT_DIR/" "$REMOTE_USER@$KHADAS_IP:$REMOTE_STAGING_DIR/"

# 2. Create .env on remote for docker-compose.test.yml
echo "🔧 Setting up staging environment..."
sshpass -e ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$KHADAS_IP" "
    cd $REMOTE_STAGING_DIR

    # Root .env for docker-compose variable substitution
    cat <<EOT > .env
GEMINI_API_KEY=$GEMINI_KEY
RESEND_API_KEY=$RESEND_KEY
EMAIL_SENDER=
EMAIL_RECIPIENTS=
EOT

    # Backend .env
    cat <<EOT > backend/.env
DATABASE_URL=postgresql://user:password@test-db:5432/arxiv_test_db
PDF_SAVE_DIR=/app/data
AI_PROVIDER=gemini
GEMINI_API_KEY=$GEMINI_KEY
EOT
"

# 3. Build and run staging stack
echo "🏗️  Building and running STAGING containers..."
sshpass -e ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$KHADAS_IP" << 'EOF'
    set -ex
    SSHPASS="khadas"
    cd ~/arxiv_assistant_staging

    # Stop any existing staging containers
    echo "$SSHPASS" | sudo -S docker compose -f docker-compose.test.yml down --remove-orphans 2>/dev/null || true

    # Build and start staging
    echo "$SSHPASS" | sudo -S docker compose -f docker-compose.test.yml up -d --build --force-recreate

    # Wait for DB
    echo "⏳ Waiting for staging database..."
    for i in {1..20}; do
        if echo "$SSHPASS" | sudo -S docker exec arxiv_test_db pg_isready -U user -d arxiv_test_db 2>/dev/null; then
            echo "✅ Staging DB ready."
            break
        fi
        echo "Waiting... ($i/20)"
        sleep 3
    done

    # Ensure pgvector extension
    echo "$SSHPASS" | sudo -S docker exec arxiv_test_db psql -U user -d arxiv_test_db -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true
EOF

# 4. Health check
echo "🌐 Testing staging API (http://$KHADAS_IP:8001/)..."
MAX_RETRIES=5
RETRY_COUNT=0
HEALTHY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    set +e
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$KHADAS_IP:8001/" 2>/dev/null)
    set -e

    if [ "$HTTP_STATUS" == "200" ]; then
        HEALTHY=true
        echo "✅ Staging API is healthy (HTTP $HTTP_STATUS)"
        break
    fi

    echo "⏳ Attempt $((RETRY_COUNT+1)) — HTTP $HTTP_STATUS. Waiting 5s..."
    RETRY_COUNT=$((RETRY_COUNT+1))
    sleep 5
done

if [ "$HEALTHY" = false ]; then
    echo "❌ Staging health check failed after $MAX_RETRIES attempts."
    echo "📜 Staging backend logs:"
    sshpass -e ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$KHADAS_IP" \
        "cd ~/arxiv_assistant_staging && sudo docker compose -f docker-compose.test.yml logs --tail 50 test-backend"
    exit 1
fi

echo ""
echo "============================================"
echo "✅ STAGING deployment complete!"
echo "   Frontend: http://$KHADAS_IP:3001"
echo "   Backend:  http://$KHADAS_IP:8001/docs"
echo "   DB:       $KHADAS_IP:5435"
echo ""
echo "   To tear down staging:"
echo "   ssh $REMOTE_USER@$KHADAS_IP 'cd ~/arxiv_assistant_staging && sudo docker compose -f docker-compose.test.yml down -v'"
echo "============================================"
