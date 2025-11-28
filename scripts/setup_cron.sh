#!/bin/bash
# Setup automated 2x daily pipeline runs for data collection sprint
# This script configures cron to run the pipeline twice daily (9 AM and 9 PM)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "RKL Phase-0 Cron Automation Setup"
echo "=========================================="
echo ""
echo "Project directory: $PROJECT_DIR"
echo ""

# Check that we're in the right place
if [ ! -f "$PROJECT_DIR/scripts/fetch_and_summarize.py" ]; then
    echo "❌ Error: Cannot find fetch_and_summarize.py"
    echo "   Make sure you're running from the project root"
    exit 1
fi

# Create log directory
LOG_DIR="$PROJECT_DIR/logs/cron"
mkdir -p "$LOG_DIR"

echo "📁 Created log directory: $LOG_DIR"
echo ""

# Create wrapper script for cron (handles PATH and environment)
WRAPPER_SCRIPT="$PROJECT_DIR/scripts/cron_pipeline_wrapper.sh"
cat > "$WRAPPER_SCRIPT" <<'EOF'
#!/bin/bash
# Wrapper script for cron - sets up environment and runs pipeline

# Set PATH to include common locations
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin:$PATH"

# Change to project directory
cd "$(dirname "$0")/.."

# Create timestamp for this run
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
LOG_FILE="logs/cron/pipeline_$TIMESTAMP.log"

echo "=========================================" >> "$LOG_FILE"
echo "Pipeline Run: $TIMESTAMP" >> "$LOG_FILE"
echo "=========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Run pipeline with output captured
python3 scripts/fetch_and_summarize.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "" >> "$LOG_FILE"
echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"

# If successful, run health check
if [ $EXIT_CODE -eq 0 ]; then
    echo "" >> "$LOG_FILE"
    echo "Running health check..." >> "$LOG_FILE"
    python3 scripts/health_check.py >> "$LOG_FILE" 2>&1
else
    echo "⚠️  Pipeline failed - skipping health check" >> "$LOG_FILE"
fi

# Keep only last 30 days of logs
find logs/cron -name "pipeline_*.log" -mtime +30 -delete 2>/dev/null || true

exit $EXIT_CODE
EOF

chmod +x "$WRAPPER_SCRIPT"
echo "✅ Created wrapper script: $WRAPPER_SCRIPT"
echo ""

# Check if cron entries already exist
if crontab -l 2>/dev/null | grep -q "rkl-phase0-morning"; then
    echo "⚠️  Cron entries already exist. Remove them first with:"
    echo "   crontab -e"
    echo ""
    echo "Current cron entries:"
    crontab -l 2>/dev/null | grep "rkl-phase0"
    echo ""
    read -p "Remove existing entries and continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted"
        exit 1
    fi

    # Remove existing entries
    crontab -l 2>/dev/null | grep -v "rkl-phase0" | crontab -
    echo "✅ Removed existing entries"
    echo ""
fi

# Add cron entries
(crontab -l 2>/dev/null; cat <<CRON

# RKL Phase-0 Data Collection (Dec 1 Sprint)
# Morning run: 9:00 AM daily
0 9 * * * $WRAPPER_SCRIPT # rkl-phase0-morning

# Evening run: 9:00 PM daily
0 21 * * * $WRAPPER_SCRIPT # rkl-phase0-evening

CRON
) | crontab -

echo "✅ Cron automation configured!"
echo ""
echo "Schedule:"
echo "  - Morning run:  9:00 AM daily"
echo "  - Evening run:  9:00 PM daily"
echo ""
echo "Logs location: $LOG_DIR/pipeline_YYYY-MM-DD_HHMMSS.log"
echo ""
echo "To verify cron setup:"
echo "  crontab -l | grep rkl-phase0"
echo ""
echo "To remove automation later:"
echo "  crontab -e"
echo "  (delete the two rkl-phase0 lines)"
echo ""
echo "=========================================="
echo "✅ AUTOMATION READY"
echo "=========================================="
echo ""
echo "Next pipeline runs:"
crontab -l | grep "rkl-phase0" | while read -r line; do
    hour=$(echo "$line" | awk '{print $2}')
    echo "  - $(date -d "$hour:00 today" "+%I:%M %p") today (if not passed)"
done
echo ""
