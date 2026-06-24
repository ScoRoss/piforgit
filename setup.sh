#!/bin/bash
# =============================================================
#  27 CARS — PI UNIT FIRST-TIME SETUP
#  Run once on a fresh Pi to get it fully operational.
#  Usage: bash setup.sh
# =============================================================

set -e

REPO_URL="https://github.com/ScoRoss/piforgit.git"
REPO_DIR="$HOME/piforgit"
SERVER_IP="100.97.37.123"
SERVER_URL="https://27carslivestream.co.uk"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   27 CARS — PI UNIT SETUP${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# --- STEP 1: UNIT ID ---
echo -e "${YELLOW}[1/6] Unit Identity${NC}"
read -p "    Enter unit number (e.g. 001, 002): " UNIT_NUM
UNIT_ID="PI_UNIT_${UNIT_NUM}"
echo -e "    Unit ID will be: ${GREEN}${UNIT_ID}${NC}"
echo ""

# --- STEP 2: DOCKER ---
echo -e "${YELLOW}[2/6] Checking Docker...${NC}"
if command -v docker &> /dev/null; then
    echo -e "    ${GREEN}Docker already installed — skipping.${NC}"
else
    echo "    Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
    echo -e "    ${GREEN}Docker installed.${NC}"
fi
echo ""

# --- STEP 3: TAILSCALE ---
echo -e "${YELLOW}[3/6] Checking Tailscale...${NC}"
if command -v tailscale &> /dev/null; then
    TS_STATE=$(sudo tailscale status --json 2>/dev/null | grep -o '"BackendState":"[^"]*"' || echo "")
    if [[ "$TS_STATE" == *"Running"* ]]; then
        echo -e "    ${GREEN}Tailscale already connected — skipping.${NC}"
    else
        echo "    Authenticating Tailscale as ${UNIT_ID}..."
        sudo tailscale up --hostname="$UNIT_ID"
        echo -e "    ${GREEN}Tailscale connected.${NC}"
    fi
else
    echo "    Installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
    echo "    Authenticating as ${UNIT_ID}..."
    sudo tailscale up --hostname="$UNIT_ID"
    echo -e "    ${GREEN}Tailscale installed and connected.${NC}"
fi
echo ""

# --- STEP 4: REPO ---
echo -e "${YELLOW}[4/6] Syncing repository...${NC}"
if [ -d "$REPO_DIR/.git" ]; then
    echo "    Repo already cloned — pulling latest..."
    cd "$REPO_DIR" && git pull origin main
else
    echo "    Cloning repo..."
    git clone "$REPO_URL" "$REPO_DIR"
fi
echo -e "    ${GREEN}Repo ready at ${REPO_DIR}${NC}"
echo ""

# --- STEP 5: ENV FILE ---
echo -e "${YELLOW}[5/6] Writing unit environment file...${NC}"
cat > "$REPO_DIR/.env" << EOF
UNIT_ID=${UNIT_ID}
SERVER_IP=${SERVER_IP}
SERVER_URL=${SERVER_URL}
EOF
echo -e "    ${GREEN}.env written:${NC}"
cat "$REPO_DIR/.env" | sed 's/^/      /'
echo ""

# --- STEP 6: CAMERA CHECK + CONTAINER ---
echo -e "${YELLOW}[6/6] Checking camera and starting container...${NC}"
if ls /dev/video0 &> /dev/null; then
    echo -e "    ${GREEN}Camera detected at /dev/video0${NC}"
else
    echo -e "    ${RED}WARNING: /dev/video0 not found. Check camera before deploying.${NC}"
fi

cd "$REPO_DIR"

# Add current user to docker group if not already (handles fresh installs)
if ! groups "$USER" | grep -q docker; then
    echo "    Adding $USER to docker group..."
    sudo usermod -aG docker "$USER"
    echo "    Running docker with sudo for this session..."
    sudo docker compose up -d --build
else
    docker compose up -d --build
fi

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}   ${UNIT_ID} IS LIVE${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo "  Tailing logs — confirm it's polling (Ctrl+C to exit):"
echo ""
sleep 2

if ! groups "$USER" | grep -q docker; then
    sudo docker compose logs -f --tail=20
else
    docker compose logs -f --tail=20
fi
