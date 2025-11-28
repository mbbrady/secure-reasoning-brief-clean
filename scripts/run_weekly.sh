#!/usr/bin/env bash
#
# RKL Secure Reasoning Brief - Weekly Pipeline Runner
# Wrapper script for cron/systemd execution
#
# This runs the Phase 1.0 simplified pipeline:
#   Step 1: Fetch and summarize articles
#   Step 2: Generate and publish brief

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/data/logs"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$LOG_DIR/weekly-${TIMESTAMP}.log"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1" | tee -a "$LOG_FILE"
}

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

log "============================================"
log "RKL Secure Reasoning Brief - Weekly Pipeline"
log "Phase 1.0: Simplified Python Implementation"
log "============================================"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    log_error "Virtual environment not found at $VENV_DIR"
    log "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install -r "$PROJECT_DIR/requirements.txt"
else
    log "Activating Python virtual environment..."
    source "$VENV_DIR/bin/activate"
fi

# Verify Ollama connectivity
log "Checking Ollama connectivity..."
if curl -s http://192.168.1.10:11434/api/tags > /dev/null 2>&1; then
    log_success "Ollama is accessible"
else
    log_error "Cannot connect to Ollama at 192.168.1.10:11434"
    log "Please ensure Ollama is running on Betty head node"
    exit 1
fi

# Step 1: Fetch and Summarize
log ""
log "Step 1: Fetching RSS feeds and generating summaries..."
log "(This uses local Ollama for AI summarization - Type III processing)"

if python3 "$SCRIPT_DIR/fetch_and_summarize.py" 2>&1 | tee -a "$LOG_FILE"; then
    log_success "Step 1 completed: Articles fetched and summarized"
else
    log_error "Step 1 failed: Could not fetch or summarize articles"
    exit 1
fi

# Step 2: Generate and Publish
log ""
log "Step 2: Generating Hugo brief and publishing..."

if python3 "$SCRIPT_DIR/publish_brief.py" 2>&1 | tee -a "$LOG_FILE"; then
    log_success "Step 2 completed: Brief generated and published"
else
    log_error "Step 2 failed: Could not generate or publish brief"
    exit 1
fi

# Summary
log ""
log "============================================"
log_success "Weekly brief generation completed successfully!"
log "============================================"
log ""
log "Output locations:"
log "  - Intermediate data: $PROJECT_DIR/content/briefs/"
log "  - Published brief: $PROJECT_DIR/../website/content/briefs/"
log "  - Log file: $LOG_FILE"
log ""

# Check publishing status
if grep -q "PUBLISH_TO_GITHUB=true" "$PROJECT_DIR/.env" 2>/dev/null; then
    log "Git publishing enabled - brief has been committed"
    if grep -q "AUTO_PUSH=true" "$PROJECT_DIR/.env" 2>/dev/null; then
        log_success "Changes pushed to remote - Netlify will auto-deploy"
    else
        log "Run 'git push' to deploy to Netlify"
    fi
else
    log "Git publishing disabled (set PUBLISH_TO_GITHUB=true in .env to enable)"
fi

log ""
log "Type III Secure Reasoning:"
log "  ✓ All processing occurred locally on Betty cluster"
log "  ✓ Only derived insights were published"
log "  ✓ Raw data remains under local control"
log "  ✓ Complete audit trail maintained"
log ""
log_success "Weekly brief generation complete! 🎉"

exit 0
