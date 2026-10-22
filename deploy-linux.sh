#!/bin/bash
set -e

# Configuration (override with environment variables)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KHADAS_IP="${KHADAS_IP:-192.168.1.49}"
FRAMEWORK_IP="${FRAMEWORK_IP:-192.168.1.32}"
PROJECT_DIR="${PROJECT_DIR:-$SCRIPT_DIR}"
REMOTE_USER="${KHADAS_USER:-khadas}"
export SSHPASS="${KHADAS_PASSWORD:-khadas}"

echo "🚀 Starting Linux Deployment to Khadas Edge 2 ($KHADAS_IP)..."
echo "   Source directory: $PROJECT_DIR"

read_local_key() {
    local key_name="$1"
    local val=""
    if [ -f "$PROJECT_DIR/backend/.env" ]; then
        val=$(grep "^${key_name}=" "$PROJECT_DIR/backend/.env" 2>/dev/null | tail -n1 | cut -d'=' -f2- | tr -d '"' || true)
    fi
    if [ -z "$val" ] && [ -f "$PROJECT_DIR/.env" ]; then
        val=$(grep "^${key_name}=" "$PROJECT_DIR/.env" 2>/dev/null | tail -n1 | cut -d'=' -f2- | tr -d '"' || true)
    fi
    echo "$val"
}

read_remote_key() {
    local key_name="$1"
    sshpass -e ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$KHADAS_IP" "
        val=\$(grep '^${key_name}=' ~/arxiv_assistant/.env 2>/dev/null | tail -n1 | cut -d'=' -f2- | tr -d '\"' || true)
        if [ -z \"\$val\" ]; then
            val=\$(grep '^${key_name}=' ~/arxiv_assistant/backend/.env 2>/dev/null | tail -n1 | cut -d'=' -f2- | tr -d '\"' || true)
        fi
        echo \"\$val\"
    "
}

resolve_key() {
    local key_name="$1"
    local val
    val=$(read_local_key "$key_name")
    if [ -z "$val" ]; then
        val=$(read_remote_key "$key_name")
    fi
    echo "$val"
}

# 0. Resolve API keys from local .env files or fallback to existing remote .env on Khadas
GEMINI_KEY=$(resolve_key "GEMINI_API_KEY")
RESEND_KEY=$(resolve_key "RESEND_API_KEY")
LITELLM_KEY=$(resolve_key "LITELLM_API_KEY")
NVIDIA_KEY=$(resolve_key "NVIDIA_API_KEY")

if [ -z "$LITELLM_KEY" ]; then
    echo "❌ LITELLM_API_KEY not found in local $PROJECT_DIR/.env or remote ~/arxiv_assistant/.env — aborting."
    exit 1
fi

# 1. Install Docker on Khadas (if not present)
echo "🐳 Checking Docker on Khadas..."
sshpass -e ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$KHADAS_IP" '
    if ! command -v docker &> /dev/null; then
        echo "Docker not found. Installing..."
        echo "khadas" | sudo -S sh -c "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
        echo "khadas" | sudo -S usermod -aG docker $USER
    else
        echo "Docker is already installed."
    fi
'

# 2. Sync files using rsync with RSYNC_RSH to ensure protocol stability
echo "📂 Syncing files to Khadas..."
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
    --exclude '.venv' \
    "$PROJECT_DIR/" "$REMOTE_USER@$KHADAS_IP:~/arxiv_assistant/"

# 2b. Clean up old models.py (replaced by models/ package)
sshpass -e ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$KHADAS_IP" \
    "rm -f ~/arxiv_assistant/backend/models.py ~/arxiv_assistant/backend/models_orig.py"

# 3. Handle Environment Variables (Frontend/Backend)
echo "🔧 Updating remote .env files..."
sshpass -e ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$KHADAS_IP" "
    cat <<EOT > ~/arxiv_assistant/backend/.env
DATABASE_URL=postgresql://user:password@db:5432/arxiv_db
PDF_SAVE_DIR=/app/data/pdfs
CHROME_PATH=/usr/bin/google-chrome
GEMINI_API_KEY=$GEMINI_KEY
LITELLM_API_KEY=$LITELLM_KEY
NVIDIA_API_KEY=$NVIDIA_KEY
EOT
    echo GEMINI_API_KEY=$GEMINI_KEY > ~/arxiv_assistant/.env
    echo RESEND_API_KEY=$RESEND_KEY >> ~/arxiv_assistant/.env
    echo LITELLM_API_KEY=$LITELLM_KEY >> ~/arxiv_assistant/.env
    echo NVIDIA_API_KEY=$NVIDIA_KEY >> ~/arxiv_assistant/.env
    echo FRAMEWORK_IP=$FRAMEWORK_IP >> ~/arxiv_assistant/.env
    echo FRONTEND_URL=http://$KHADAS_IP:3000 >> ~/arxiv_assistant/.env
"

# 4. Build and Run
echo "🏗️  Building and Running Containers..."
sshpass -e ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$KHADAS_IP" << 'EOF'
    set -ex
    cd ~/arxiv_assistant

    SSHPASS="khadas"
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.khadas-ollama.yml"

    # --- DB Storage Setup (Loopback for exFAT compatibility) ---
    IMG_PATH="/media/khadas/External1/postgres.img"
    MOUNT_POINT="/media/khadas/External1/arxiv_data/postgres"

    echo "⚙️ Setting up database storage..."
    if [ ! -f "$IMG_PATH" ]; then
        echo "Creating new 10GB database disk image..."
        echo "$SSHPASS" | sudo -S dd if=/dev/zero of="$IMG_PATH" bs=1M count=10240 status=progress
        echo "$SSHPASS" | sudo -S mkfs.ext4 "$IMG_PATH"
    fi

    mkdir -p "$MOUNT_POINT"
    if ! mountpoint -q "$MOUNT_POINT"; then
        echo "Mounting database image..."
        if ! echo "$SSHPASS" | sudo -S mount -o loop "$IMG_PATH" "$MOUNT_POINT"; then
            echo "❌ ERROR: Failed to mount database image at $MOUNT_POINT!"
            exit 1
        fi
        echo "$SSHPASS" | sudo -S chown -R 1000:1000 "$MOUNT_POINT"
    else
        echo "✅ Database image already mounted at $MOUNT_POINT."
    fi
    # -----------------------------------------------------------

    DATA_DIR_PATH="/media/khadas/External1/PDFs/Arxiv Assistant"
    echo "DATA_DIR=\"$DATA_DIR_PATH\"" >> .env
    echo "DB_STORAGE=\"$MOUNT_POINT\"" >> .env

    echo "🔍 Verifying Docker Compose configuration..."
    echo "$SSHPASS" | sudo -S env DATA_DIR="$DATA_DIR_PATH" DB_STORAGE="$MOUNT_POINT" docker compose $COMPOSE_FILES --env-file .env config >/dev/null

    # Build backend, worker (reuses backend layers), and frontend one by one BEFORE stopping containers
    echo "$SSHPASS" | sudo -S env DATA_DIR="$DATA_DIR_PATH" DB_STORAGE="$MOUNT_POINT" docker compose $COMPOSE_FILES --env-file .env build backend
    echo "$SSHPASS" | sudo -S env DATA_DIR="$DATA_DIR_PATH" DB_STORAGE="$MOUNT_POINT" docker compose $COMPOSE_FILES --env-file .env build worker
    echo "$SSHPASS" | sudo -S env DATA_DIR="$DATA_DIR_PATH" DB_STORAGE="$MOUNT_POINT" docker compose $COMPOSE_FILES --env-file .env build frontend

    echo "$SSHPASS" | sudo -S env DATA_DIR="$DATA_DIR_PATH" DB_STORAGE="$MOUNT_POINT" docker compose $COMPOSE_FILES --env-file .env down --remove-orphans

    echo "🗄️  Bringing up db + backend only (pre-migration, MIGRATING=1)..."
    echo "$SSHPASS" | sudo -S env DATA_DIR="$DATA_DIR_PATH" DB_STORAGE="$MOUNT_POINT" MIGRATING=1 docker compose $COMPOSE_FILES --env-file .env up -d --force-recreate db backend

    echo "🔍 Verifying internal schema version..."
    echo "$SSHPASS" | sudo -S docker exec arxiv_assistant_backend cat /app/schemas.py | grep "Any" || echo "❌ WARNING: 'Any' type not found in container's schemas.py!"

    # 5. Database Migration (New entities column and search index)
    echo "🛠️ Running database migrations and verification..."

    echo "⏳ Waiting for database to be ready..."
    for i in {1..30}; do
        if echo "$SSHPASS" | sudo -S docker exec arxiv_assistant_db pg_isready -U user -d arxiv_db; then
            break
        fi
        echo "Waiting for Postgres... ($i/30)"
        sleep 2
    done

    echo "🏗️ Checking database extensions..."
    echo "$SSHPASS" | sudo -S docker exec arxiv_assistant_db psql -U user -d arxiv_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

    echo "📊 Database Stats:"
    echo "$SSHPASS" | sudo -S docker exec arxiv_assistant_db psql -U user -d arxiv_db -c "SELECT count(*) as paper_count FROM papers;" || echo "Failed to count papers."

    echo "$SSHPASS" | sudo -S docker exec arxiv_assistant_db psql -U user -d arxiv_db -c "ALTER TABLE papers ADD COLUMN IF NOT EXISTS entities JSONB;"
    echo "$SSHPASS" | sudo -S docker exec arxiv_assistant_db psql -U user -d arxiv_db -c "ALTER TABLE papers ADD COLUMN IF NOT EXISTS in_drive_details JSONB;"
    echo "$SSHPASS" | sudo -S docker exec arxiv_assistant_db psql -U user -d arxiv_db -c "
        DO \$\$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='papers' AND column_name='search_vector' AND is_generated='ALWAYS'
            ) THEN
                DROP INDEX IF EXISTS idx_papers_search;
                ALTER TABLE papers DROP COLUMN IF EXISTS search_vector;
                ALTER TABLE papers ADD COLUMN search_vector tsvector GENERATED ALWAYS AS (
                    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
                    setweight(to_tsvector('english', coalesce(summary, '')), 'B') ||
                    setweight(to_tsvector('english', coalesce(entities::text, '')), 'A')
                ) STORED;
                CREATE INDEX idx_papers_search ON papers USING GIN(search_vector);
            END IF;
        END \$\$;
    "

    echo "🛠️ Running reading queue migration..."
    echo "$SSHPASS" | sudo -S docker exec arxiv_assistant_backend python migrate_reading_queue.py

    echo "🛠️ Running summary status migration..."
    echo "$SSHPASS" | sudo -S docker exec arxiv_assistant_backend python migrate_add_summary_status.py

    echo "🛠️ Running full-text extraction migration..."
    echo "$SSHPASS" | sudo -S docker exec arxiv_assistant_db psql -U user -d arxiv_db -c "ALTER TABLE papers ADD COLUMN IF NOT EXISTS full_text_sections JSONB;"
    echo "$SSHPASS" | sudo -S docker exec arxiv_assistant_db psql -U user -d arxiv_db -c "ALTER TABLE papers ADD COLUMN IF NOT EXISTS extracted_images JSONB;"

    echo "🚀 Migrations complete — bringing up worker + frontend (MIGRATING unset)..."
    echo "$SSHPASS" | sudo -S env DATA_DIR="$DATA_DIR_PATH" DB_STORAGE="$MOUNT_POINT" docker compose $COMPOSE_FILES --env-file .env up -d

    # Final API Health Check with Retries
    echo "🌐 Testing API endpoint (http://localhost:8000/papers/)..."
    MAX_RETRIES=5
    RETRY_COUNT=0
    HEALTHY=false

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        set +e
        API_CHECK=$(echo "$SSHPASS" | sudo -S docker exec arxiv_assistant_backend curl -s -w "\n%{http_code}" 'http://localhost:8000/papers/?limit=100')
        set -e

        HTTP_STATUS=$(echo "$API_CHECK" | tail -n1)
        BODY=$(echo "$API_CHECK" | head -n -1)

        if [ "$HTTP_STATUS" == "200" ]; then
            HEALTHY=true
            echo "✅ API is Healthy. Sample Data Received:"
            echo "$BODY" | head -n 20
            break
        fi

        echo "⏳ Attempt $((RETRY_COUNT+1)) failed with status $HTTP_STATUS. Waiting 5s..."
        RETRY_COUNT=$((RETRY_COUNT+1))
        sleep 5
    done

    if [ "$HEALTHY" = false ]; then
        echo "❌ API Health Check FAILED after $MAX_RETRIES attempts (Last Status: $HTTP_STATUS)"
        echo "$SSHPASS" | sudo -S docker compose $COMPOSE_FILES logs --tail 200 backend
        echo "$SSHPASS" | sudo -S docker compose $COMPOSE_FILES ps
        exit 1
    else
        echo "✅ API is active and healthy."
    fi

    echo "💾 Verifying Docker volume mount..."
    echo "$SSHPASS" | sudo -S docker inspect arxiv_assistant_db | grep -A 10 "Mounts"
EOF

echo "✅ Deployment completed successfully!"
