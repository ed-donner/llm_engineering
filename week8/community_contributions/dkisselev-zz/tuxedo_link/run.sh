#!/bin/bash
# Launch script for Tuxedo Link

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎩 Tuxedo Link - AI-Powered Cat Adoption Search${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Please run setup first:${NC}"
    echo "   uv venv && source .venv/bin/activate && uv pip install -e \".[dev]\""
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}✓${NC} Activating virtual environment..."
source .venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    if [ -f "env.example" ]; then
        cp env.example .env
        echo -e "${YELLOW}Please edit .env with your API keys before continuing.${NC}"
        exit 1
    fi
fi

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo -e "${YELLOW}⚠️  config.yaml not found. Creating from example...${NC}"
    if [ -f "config.example.yaml" ]; then
        cp config.example.yaml config.yaml
        echo -e "${GREEN}✓${NC} config.yaml created. Review settings if needed."
    fi
fi

# Check deployment mode from config
DEPLOYMENT_MODE=$(python -c "import yaml; config = yaml.safe_load(open('config.yaml')); print(config['deployment']['mode'])" 2>/dev/null || echo "local")

if [ "$DEPLOYMENT_MODE" = "production" ]; then
    echo -e "${BLUE}📡 Production mode enabled${NC}"
    echo "   UI will connect to Modal backend"
    echo "   All searches and agents run on Modal"
    echo ""
else
    echo -e "${GREEN}💻 Local mode enabled${NC}"
    echo "   All components run locally"
    echo ""
fi

# Check for required API keys
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null && ! grep -q "PETFINDER_API_KEY" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Please configure API keys in .env file${NC}"
    echo "   Required: OPENAI_API_KEY, PETFINDER_API_KEY"
    exit 1
fi

echo -e "${GREEN}✓${NC} Environment configured"

# Initialize databases if needed
if [ ! -f "data/tuxedo_link.db" ]; then
    echo -e "${GREEN}✓${NC} Initializing databases..."
    python setup_vectordb.py > /dev/null 2>&1
fi

echo -e "${GREEN}✓${NC} Databases ready"
echo ""
echo -e "${BLUE}🚀 Starting Tuxedo Link...${NC}"
echo ""
echo -e "   ${GREEN}→${NC} Opening http://localhost:7860"
echo -e "   ${GREEN}→${NC} Press Ctrl+C to stop"
echo ""

# Launch the app
python app.py

