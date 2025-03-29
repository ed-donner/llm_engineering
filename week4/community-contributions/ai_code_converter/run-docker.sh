#!/bin/bash
#
# CodeXchange AI Docker Wrapper Script
# This script simplifies running the CodeXchange AI application using Docker.
#

set -e

# Color codes for terminal output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script version
VERSION="1.0.0"

# Default values
ENV_FILE=".env"
PORT=7860
BUILD_ONLY=false
DETACHED=false
FOLLOW_LOGS=false
STOP=false
RESTART=false
DOWN=false
API_KEY_REMIND=false

# Display script banner
display_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════╗"
    echo "║        CodeXchange AI - Docker Launcher           ║"
    echo "╚═══════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Display help message
display_help() {
    echo -e "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -b, --build        Build the Docker image without running the container"
    echo "  -d, --detach       Run container in detached mode (background)"
    echo "  -e, --env FILE     Specify an environment file (default: .env)"
    echo "  -p, --port PORT    Specify the port to expose (default: 7860)"
    echo "  -l, --logs         Follow the container logs after starting"
    echo "  -s, --stop         Stop the running container"
    echo "  -r, --restart      Restart the container"
    echo "  -D, --down         Stop and remove the container"
    echo "  -k, --keys         Check for API keys and show setup instructions if missing"
    echo "  -h, --help         Display this help message"
    echo "  -v, --version      Display script version"
    echo
    echo "Examples:"
    echo "  $0                 Build and run the container"
    echo "  $0 -d -p 8080      Run in detached mode on port 8080"
    echo "  $0 -b              Build the image only"
    echo "  $0 -s              Stop the running container"
    echo
}

# Check prerequisites
check_prerequisites() {
    echo -e "${BLUE}Checking prerequisites...${NC}"
    
    # Check for Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed or not in PATH.${NC}"
        echo "Please install Docker to continue: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check for docker-compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${YELLOW}Warning: docker-compose not found. Checking for Docker Compose V2...${NC}"
        if ! docker compose version &> /dev/null; then
            echo -e "${RED}Error: Docker Compose not found.${NC}"
            echo "Please install Docker Compose to continue: https://docs.docker.com/compose/install/"
            exit 1
        else
            echo -e "${GREEN}Docker Compose V2 found.${NC}"
            COMPOSE_CMD="docker compose"
        fi
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    echo -e "${GREEN}Prerequisites satisfied.${NC}"
}

# Check for environment variables
check_env_file() {
    # Check if the specified .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}Warning: $ENV_FILE file not found.${NC}"
        
        # If it's the default .env and .env.example exists, offer to copy it
        if [ "$ENV_FILE" = ".env" ] && [ -f ".env.example" ]; then
            echo -e "Would you like to create a .env file from .env.example? (y/n)"
            read -r response
            if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                cp .env.example .env
                echo -e "${GREEN}.env file created from .env.example. Please edit it to add your API keys.${NC}"
                API_KEY_REMIND=true
            fi
        else
            echo -e "${YELLOW}Please create an environment file with your API keys.${NC}"
            API_KEY_REMIND=true
        fi
    fi
}

# Check for required API keys
check_api_keys() {
    if [ "$API_KEY_REMIND" = true ] || [ "$1" = true ]; then
        echo -e "${YELLOW}API Key Requirements:${NC}"
        echo "The CodeXchange AI requires API keys for the following services:"
        echo "  - OPENAI_API_KEY (Required for OpenAI GPT models)"
        echo "  - ANTHROPIC_API_KEY (Required for Claude models)"
        echo "  - GOOGLE_API_KEY (Required for Google Gemini models)"
        echo "  - DEEPSEEK_API_KEY (Required for DeepSeek models)"
        echo "  - GROQ_API_KEY (Required for GROQ models)"
        echo
        echo -e "Please ensure these keys are set in your ${BLUE}$ENV_FILE${NC} file."
        echo "You only need keys for the models you plan to use."
    fi
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -b|--build)
                BUILD_ONLY=true
                shift
                ;;
            -d|--detach)
                DETACHED=true
                shift
                ;;
            -e|--env)
                ENV_FILE="$2"
                shift 2
                ;;
            -p|--port)
                PORT="$2"
                shift 2
                ;;
            -l|--logs)
                FOLLOW_LOGS=true
                shift
                ;;
            -s|--stop)
                STOP=true
                shift
                ;;
            -r|--restart)
                RESTART=true
                shift
                ;;
            -D|--down)
                DOWN=true
                shift
                ;;
            -k|--keys)
                check_api_keys true
                exit 0
                ;;
            -h|--help)
                display_banner
                display_help
                exit 0
                ;;
            -v|--version)
                echo "CodeXchange AI Docker Wrapper v$VERSION"
                exit 0
                ;;
            *)
                echo -e "${RED}Error: Unknown option $1${NC}"
                display_help
                exit 1
                ;;
        esac
    done
}

# Build the Docker image
build_image() {
    echo -e "${BLUE}Building the Docker image...${NC}"
    
    # Export PORT from the environment for docker-compose
    export PORT=$PORT
    
    if [ -f "$ENV_FILE" ]; then
        echo -e "${GREEN}Using environment file: $ENV_FILE${NC}"
        OPTS="--env-file $ENV_FILE"
    else
        OPTS=""
    fi
    
    # Build the image
    $COMPOSE_CMD $OPTS build
    
    echo -e "${GREEN}Docker image built successfully.${NC}"
}

# Run the container
run_container() {
    echo -e "${BLUE}Starting the CodeXchange AI...${NC}"
    
    # Export PORT from the environment for docker-compose
    export PORT=$PORT
    
    if [ -f "$ENV_FILE" ]; then
        OPTS="--env-file $ENV_FILE"
    else
        OPTS=""
    fi
    
    # Add detach flag if specified
    if [ "$DETACHED" = true ]; then
        OPTS="$OPTS -d"
    fi
    
    # Run the container
    $COMPOSE_CMD $OPTS up
    
    # Follow logs if detached and requested
    if [ "$DETACHED" = true ] && [ "$FOLLOW_LOGS" = true ]; then
        $COMPOSE_CMD logs -f
    fi
}

# Stop the container
stop_container() {
    echo -e "${BLUE}Stopping the CodeXchange AI...${NC}"
    $COMPOSE_CMD stop
    echo -e "${GREEN}Container stopped.${NC}"
}

# Restart the container
restart_container() {
    echo -e "${BLUE}Restarting the CodeXchange AI...${NC}"
    $COMPOSE_CMD restart
    echo -e "${GREEN}Container restarted.${NC}"
    
    if [ "$FOLLOW_LOGS" = true ]; then
        $COMPOSE_CMD logs -f
    fi
}

# Bring down the container
down_container() {
    echo -e "${BLUE}Stopping and removing the CodeXchange AI container...${NC}"
    $COMPOSE_CMD down
    echo -e "${GREEN}Container stopped and removed.${NC}"
}

# Display access information
display_access_info() {
    echo -e "${GREEN}The CodeXchange AI is running!${NC}"
    echo -e "Access the application at: ${BLUE}http://localhost:$PORT${NC}"
    
    # Check if port is custom and update info
    if [ "$PORT" != "7860" ]; then
        echo -e "Running on custom port: ${BLUE}$PORT${NC}"
    fi
    
    # If running detached, provide instructions for logs
    if [ "$DETACHED" = true ]; then
        echo -e "Running in detached mode. Use ${YELLOW}$0 --logs${NC} to follow logs."
    fi
    
    echo -e "To stop the application, press ${YELLOW}Ctrl+C${NC} or run ${YELLOW}$0 --stop${NC}"
}

# Main function
main() {
    display_banner
    check_prerequisites
    parse_arguments "$@"
    
    if [ "$DOWN" = true ]; then
        down_container
        exit 0
    fi
    
    if [ "$STOP" = true ]; then
        stop_container
        exit 0
    fi
    
    if [ "$RESTART" = true ]; then
        restart_container
        exit 0
    fi
    
    check_env_file
    check_api_keys
    
    build_image
    
    if [ "$BUILD_ONLY" = false ]; then
        run_container
        
        # Only display access info if not in detached mode or if following logs
        if [ "$DETACHED" = false ] || [ "$FOLLOW_LOGS" = true ]; then
            display_access_info
        fi
    else
        echo -e "${GREEN}Build completed successfully. Use $0 to run the application.${NC}"
    fi
}

# Run main function with all arguments
main "$@"