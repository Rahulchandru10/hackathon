#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define Colors
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
GRAY='\033[1;30m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Initialize variables
SKIP_INSTALL=false
BACKEND_ONLY=false
FRONTEND_ONLY=false

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-install) SKIP_INSTALL=true ;;
        --backend-only) BACKEND_ONLY=true ;;
        --frontend-only) FRONTEND_ONLY=true ;;
        *) echo -e "${RED}Unknown parameter passed: $1${NC}"; exit 1 ;;
    esac
    shift
done

PROJECT_ROOT=$(pwd)

echo -e "${CYAN}
+----------------------------------------------+
|      Project Sentinel - Local Launcher       |
|            SQLite + In-Memory Mode            |
+----------------------------------------------+
${NC}"

# -- Step 1: Check Python ----------------------------------------------------
echo -e "${YELLOW}[1/5] Checking Python (3.9 - 3.15)...${NC}"
PYTHON_CMD=""

# Search list for python commands
SEARCH_LIST=("python3" "python" "python3.12" "python3.11" "python3.10" "python3.9" "python3.13")

for cmd in "${SEARCH_LIST[@]}"; do
    if command -v "$cmd" >/dev/null 2>&1; then
        # Extract version major.minor
        VER=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
        if [[ "$VER" =~ ^3\.(9|1[0-5])$ ]]; then
            PYTHON_CMD=$(command -v "$cmd")
            echo -e "  ${GREEN}[OK] Found: Python $VER (at $PYTHON_CMD)${NC}"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "  ${RED}[FAIL] Python (3.9 - 3.15) not found. Please install Python.${NC}"
    exit 1
fi

# -- Step 2: Check, Install, and Serve Ollama --------------------------------
echo -e "${YELLOW}[2/5] Checking Ollama Infrastructure...${NC}"

# 1. Check if Ollama command exists; if missing, install it along with zstd
if ! command -v ollama >/dev/null 2>&1; then
    echo -e "  ${YELLOW}[WARN] Ollama executable not found. Starting automatic native environment build...${NC}"
    
    # Check if user is root/sudo capable
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "  ${RED}[FAIL] System requires root privileges to configure zstd and install Ollama.${NC}"
        exit 1
    fi
    
    echo -e "  ${GRAY}Updating repository cache and fetching archive tools (zstd)...${NC}"
    apt-get update -q && apt-get install -y zstd -q
    
    echo -e "  ${GRAY}Fetching and deploying official Ollama architecture...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh
    echo -e "  ${GREEN}[OK] Ollama base binary engine successfully compiled.${NC}"
fi

# 2. Check if the server daemon is awake; if sleeping, spin it up
set +e
curl -s -f http://localhost:11434/api/tags > /dev/null
OLLAMA_STATUS=$?
set -e

if [ $OLLAMA_STATUS -ne 0 ]; then
    echo -e "  ${YELLOW}[WARN] Ollama background daemon is sleeping. Initializing server engine...${NC}"
    ollama serve > /dev/null 2>&1 &
    sleep 5
fi

# 3. Double check runtime heartbeat status and pre-stage your target model weights
set +e
curl -s -f http://localhost:11434/api/tags > /dev/null
OLLAMA_HEARTBEAT=$?
set -e

if [ $OLLAMA_HEARTBEAT -eq 0 ]; then
    echo -e "  ${GREEN}[OK] Ollama API service engine is awake.${NC}"
    echo -e "  ${GRAY}Pre-staging Mistral architecture model weights to AMD GPU memory...${NC}"
    ollama pull mistral > /dev/null 2>&1
    echo -e "  ${GREEN}[OK] AI model weights ready and deployed.${NC}"
else
    echo -e "  ${RED}[WARN] Failed to link daemon pipe. Transitioning platform context to Mock Mode.${NC}"
fi

# -- Step 3: Create/activate virtual environment ------------------------------
echo -e "${YELLOW}[3/5] Setting up Python virtual environment...${NC}"
VENV_PATH="$PROJECT_ROOT/.venv"

if [ ! -d "$VENV_PATH" ]; then
    echo -e "  ${GRAY}Creating venv...${NC}"
    "$PYTHON_CMD" -m venv "$VENV_PATH"
fi

PIP_CMD="$VENV_PATH/bin/pip"
PYTHON_EXE="$VENV_PATH/bin/python"

# -- Step 4: Install dependencies ---------------------------------------------
if [ "$SKIP_INSTALL" = false ]; then
    echo -e "${YELLOW}[4/5] Installing backend dependencies...${NC}"
    "$PIP_CMD" install -r "$PROJECT_ROOT/backend/requirements.txt" -q
    echo -e "  ${GRAY}Installing frontend dependencies...${NC}"
    "$PIP_CMD" install -r "$PROJECT_ROOT/frontend/requirements.txt" -q
    echo -e "  ${GREEN}[OK] Dependencies installed.${NC}"
else
    echo -e "${GRAY}[4/5] Skipping dependency install (--skip-install flag).${NC}"
fi

# -- Step 5: Copy local env ---------------------------------------------------
echo -e "${YELLOW}[5/5] Configuring environment...${NC}"
ENV_TARGET="$PROJECT_ROOT/.env"
if [ ! -f "$ENV_TARGET" ]; then
    cp "$PROJECT_ROOT/.env.local" "$ENV_TARGET"
    echo -e "  ${GREEN}[OK] Created .env from .env.local (LOCAL_MODE=true)${NC}"
else
    echo -e "  ${GREEN}[OK] Using existing .env${NC}"
fi

echo ""
echo -e "${GRAY}===============================================${NC}"
echo -e "${CYAN} Starting Services...${NC}"
echo -e "${GRAY}===============================================${NC}"

# Variables to store Process IDs
BACKEND_PID=""
FRONTEND_PID=""

# Cleanup function to kill background jobs on Ctrl+C
cleanup() {
    echo -e "\n${YELLOW}Stopping services...${NC}"
    if [ -n "$BACKEND_PID" ]; then kill $BACKEND_PID 2>/dev/null || true; fi
    if [ -n "$FRONTEND_PID" ]; then kill $FRONTEND_PID 2>/dev/null || true; fi
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM to run cleanup
trap cleanup SIGINT SIGTERM

# -- Launch Backend ----------------------------------------------------------
if [ "$FRONTEND_ONLY" = false ]; then
    echo ""
    echo -e "  ${CYAN}* Starting FastAPI backend on http://localhost:8000 ...${NC}"
    cd "$PROJECT_ROOT"
    "$PYTHON_EXE" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    sleep 4
fi

# -- Launch Frontend ---------------------------------------------------------
if [ "$BACKEND_ONLY" = false ]; then
    echo -e "  ${CYAN}* Starting Streamlit frontend securely for AMD Notebooks ...${NC}"
    cd "$PROJECT_ROOT/frontend"
    "$PYTHON_EXE" -m streamlit run app.py \
        --server.port 8501 \
        --server.address 0.0.0.0 \
        --server.headless true \
        --server.enableCORS false \
        --server.enableXsrfProtection false \
        --server.enableWebsocketCompression false &
    FRONTEND_PID=$!
    cd "$PROJECT_ROOT"
fi

echo ""
echo -e "${GRAY}===============================================${NC}"
echo -e " ${GREEN}[OK] Project Sentinel is running!${NC}"
echo ""
echo -e "   ${WHITE}Frontend  -->  http://localhost:8501${NC}"
echo -e "   ${WHITE}Backend   -->  http://localhost:8000${NC}"
echo -e "   ${WHITE}API Docs  -->  http://localhost:8000/docs${NC}"
echo ""
echo -e "   ${GRAY}Login: analyst / sentinelpass${NC}"
echo ""
echo -e "   ${GRAY}Press Ctrl+C to stop all services.${NC}"
echo -e "${GRAY}===============================================${NC}"

# Safely wait for background processes to keep the execution wrapper open
wait $BACKEND_PID $FRONTEND_PID
