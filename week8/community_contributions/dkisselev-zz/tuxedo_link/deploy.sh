#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "   Tuxedo Link - Modal Deployment"
echo "=========================================="
echo ""

# Check Modal is installed
if ! command -v modal &> /dev/null; then
    echo -e "${RED}Error: modal CLI not found${NC}"
    echo "Install with: pip install modal"
    exit 1
fi

# Check Modal auth
echo -e "${BLUE}Checking Modal authentication...${NC}"
if ! uv run python -m modal app list &>/dev/null; then
    echo -e "${RED}Error: Modal authentication not configured${NC}"
    echo "Run: uv run python -m modal setup"
    exit 1
fi
echo -e "${GREEN}✓ Modal authenticated${NC}"
echo ""

# Check config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo -e "${RED}Error: config.yaml not found${NC}"
    echo "Copy config.example.yaml to config.yaml and configure it"
    exit 1
fi

echo -e "${BLUE}Step 1: Validating configuration...${NC}"
python -c "
import yaml
import sys
try:
    config = yaml.safe_load(open('config.yaml'))
    if config['deployment']['mode'] != 'production':
        print('❌ Error: Set deployment.mode to \"production\" in config.yaml for deployment')
        sys.exit(1)
    print('✓ Configuration valid')
except Exception as e:
    print(f'❌ Error reading config: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo -e "${BLUE}Step 2: Setting up Modal secrets...${NC}"

# Check if required environment variables are set
if [ -z "$OPENAI_API_KEY" ] || [ -z "$PETFINDER_API_KEY" ] || [ -z "$MAILGUN_API_KEY" ]; then
    echo -e "${YELLOW}Warning: Some environment variables are not set.${NC}"
    echo "Make sure the following are set in your environment or .env file:"
    echo "  - OPENAI_API_KEY"
    echo "  - PETFINDER_API_KEY"
    echo "  - PETFINDER_SECRET"
    echo "  - RESCUEGROUPS_API_KEY"
    echo "  - MAILGUN_API_KEY"
    echo "  - SENDGRID_API_KEY (optional)"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Load .env if it exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

modal secret create tuxedo-link-secrets \
    OPENAI_API_KEY="${OPENAI_API_KEY}" \
    PETFINDER_API_KEY="${PETFINDER_API_KEY}" \
    PETFINDER_SECRET="${PETFINDER_SECRET}" \
    RESCUEGROUPS_API_KEY="${RESCUEGROUPS_API_KEY}" \
    MAILGUN_API_KEY="${MAILGUN_API_KEY}" \
    SENDGRID_API_KEY="${SENDGRID_API_KEY:-}" \
    --force 2>/dev/null || echo -e "${GREEN}✓ Secrets updated${NC}"

echo ""
echo -e "${BLUE}Step 3: Creating Modal volume...${NC}"
modal volume create tuxedo-link-data 2>/dev/null && echo -e "${GREEN}✓ Volume created${NC}" || echo -e "${GREEN}✓ Volume already exists${NC}"

echo ""
echo -e "${BLUE}Step 4: Copying config to Modal volume...${NC}"
# Create scripts directory if it doesn't exist
mkdir -p scripts

# Upload config.yaml to Modal volume
python scripts/upload_config_to_modal.py

echo ""
echo -e "${BLUE}Step 5: Deploying Modal API...${NC}"
modal deploy modal_services/modal_api.py

echo ""
echo -e "${BLUE}Step 6: Deploying scheduled search service...${NC}"
modal deploy modal_services/scheduled_search.py

echo ""
echo "=========================================="
echo -e "   ${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Deployed services:"
echo ""
echo "📡 Modal API (tuxedo-link-api):"
echo "  - search_cats()"
echo "  - extract_profile()"
echo "  - create_alert_and_notify()"
echo "  - get_alerts()"
echo "  - update_alert()"
echo "  - delete_alert()"
echo "  - health_check()"
echo ""
echo "⏰ Scheduled Jobs (tuxedo-link-scheduled-search):"
echo "  - daily_search_job (9 AM UTC daily)"
echo "  - weekly_search_job (Monday 9 AM UTC)"
echo "  - weekly_cleanup_job (Sunday 2 AM UTC)"
echo ""
echo "Useful commands:"
echo "  API logs:       modal app logs tuxedo-link-api --follow"
echo "  Schedule logs:  modal app logs tuxedo-link-scheduled-search --follow"
echo "  View apps:      modal app list"
echo "  View volumes:   modal volume list"
echo "  View secrets:   modal secret list"
echo ""
echo "Next steps:"
echo "  1. Run UI: ./run.sh"
echo "  2. Go to: http://localhost:7860"
echo "  3. Test search and alerts!"
echo "=========================================="

