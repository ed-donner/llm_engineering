#!/usr/bin/env bash
set -euo pipefail

# Migrate Docker named volumes to host bind-mounts
# This script copies data from old named volumes (qdrant_data, backend_data) 
# into the new host directory structure (~/RAGApp)

RAG_DATA_DIR="${RAG_DATA_DIR:-${HOME}/RAGApp}"
COMPOSE_FILE="${1:-docker/docker-compose.yml}"

echo "🔄 Migrating Docker volume data to host directories..."
echo "Target directory: $RAG_DATA_DIR"
echo ""

# Check if Docker is available
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Check if compose file exists
if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "❌ Compose file not found: $COMPOSE_FILE"
    echo "Usage: $0 [path/to/docker-compose.yml]"
    exit 1
fi

# Create target directories
mkdir -p "$RAG_DATA_DIR"
mkdir -p "$RAG_DATA_DIR/qdrant_data"

echo "📁 Created target directories"

# Function to check if a named volume exists
volume_exists() {
    docker volume ls --format "{{.Name}}" | grep -q "^$1$"
}

# Function to migrate a volume
migrate_volume() {
    local volume_name="$1"
    local target_path="$2"
    local description="$3"
    
    if volume_exists "$volume_name"; then
        echo "📦 Found volume: $volume_name"
        echo "   Copying to: $target_path"
        
        # Use a temporary container to copy data
        docker run --rm \
            -v "$volume_name":/source:ro \
            -v "$target_path":/target \
            alpine:latest \
            sh -c "cp -a /source/. /target/ 2>/dev/null || true"
        
        echo "✅ Migrated $description"
    else
        echo "ℹ️  Volume $volume_name not found (may not exist or already migrated)"
    fi
}

# Migrate Qdrant data
echo ""
echo "🔍 Checking for Qdrant volume..."
migrate_volume "rag-qdrant_qdrant_data" "$RAG_DATA_DIR/qdrant_data" "Qdrant vector database"

# Alternative Qdrant volume name patterns
migrate_volume "qdrant_data" "$RAG_DATA_DIR/qdrant_data" "Qdrant data (alt name)"
migrate_volume "docker_qdrant_data" "$RAG_DATA_DIR/qdrant_data" "Qdrant data (compose prefix)"

# Migrate backend data
echo ""
echo "🔍 Checking for backend volume..."
migrate_volume "rag-backend_backend_data" "$RAG_DATA_DIR" "backend application data"
migrate_volume "backend_data" "$RAG_DATA_DIR" "backend data (alt name)"  
migrate_volume "docker_backend_data" "$RAG_DATA_DIR" "backend data (compose prefix)"

# Check what we migrated
echo ""
echo "📊 Migration summary:"
if [[ -d "$RAG_DATA_DIR/qdrant_data" ]] && [[ "$(ls -A "$RAG_DATA_DIR/qdrant_data" 2>/dev/null)" ]]; then
    echo "✅ Qdrant data: $(du -sh "$RAG_DATA_DIR/qdrant_data" | cut -f1)"
else
    echo "ℹ️  Qdrant data: empty or not found"
fi

if [[ -d "$RAG_DATA_DIR/library" ]] && [[ "$(ls -A "$RAG_DATA_DIR/library" 2>/dev/null)" ]]; then
    echo "✅ Document library: $(find "$RAG_DATA_DIR/library" -type f | wc -l) files"
else
    echo "ℹ️  Document library: empty or not found"
fi

if [[ -d "$RAG_DATA_DIR/config" ]] && [[ "$(ls -A "$RAG_DATA_DIR/config" 2>/dev/null)" ]]; then
    echo "✅ Configuration: $(find "$RAG_DATA_DIR/config" -name "doc_*.json" | wc -l) documents"
else
    echo "ℹ️  Configuration: empty or not found"
fi

echo ""
echo "🎉 Migration complete!"
echo ""
echo "Next steps:"
echo "1. Restart your Docker stack:"
echo "   docker compose -f $COMPOSE_FILE --profile full down"
echo "   docker compose -f $COMPOSE_FILE --profile full up -d"
echo ""
echo "2. Your documents should now persist across restarts"
echo ""
echo "Optional cleanup (after verifying everything works):"
echo "   docker volume ls  # List remaining volumes"
echo "   docker volume prune  # Remove unused volumes"