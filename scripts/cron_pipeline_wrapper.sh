#!/bin/bash
# Wrapper script for cron - sets up environment and runs pipeline

# Set PATH to include common locations
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin:$PATH"

# Change to project directory
cd "$(dirname "$0")/.."

# Activate conda environment (rkl-briefs)
# Initialize conda for bash (find conda.sh in common locations)
if [ -f "$HOME/miniforge3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniforge3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "/opt/conda/etc/profile.d/conda.sh" ]; then
    source "/opt/conda/etc/profile.d/conda.sh"
fi

# Activate the rkl-briefs environment
conda activate rkl-briefs 2>/dev/null || echo "Warning: Could not activate conda environment" >&2

# Use the conda environment's python explicitly
PYTHON_BIN="$HOME/miniforge3/envs/rkl-briefs/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="/opt/conda-envs/envs/rkl-briefs/bin/python"
fi

# Create timestamp for this run
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
LOG_FILE="logs/cron/pipeline_$TIMESTAMP.log"

echo "=========================================" >> "$LOG_FILE"
echo "Pipeline Run: $TIMESTAMP" >> "$LOG_FILE"
echo "=========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Debug: Show which python we're using
echo "Python: $PYTHON_BIN" >> "$LOG_FILE"
echo "Conda env: $CONDA_DEFAULT_ENV" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Run pipeline with output captured
$PYTHON_BIN scripts/fetch_and_summarize.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "" >> "$LOG_FILE"
echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"

# If successful, run health check and generate daily brief
if [ $EXIT_CODE -eq 0 ]; then
    echo "" >> "$LOG_FILE"
    echo "Running health check..." >> "$LOG_FILE"
    $PYTHON_BIN scripts/health_check.py >> "$LOG_FILE" 2>&1

    # Generate daily brief from most recent articles JSON
    echo "" >> "$LOG_FILE"
    echo "Generating daily brief..." >> "$LOG_FILE"
    LATEST_JSON=$(ls -t content/briefs/*_articles.json 2>/dev/null | head -1)
    if [ -n "$LATEST_JSON" ]; then
        echo "Using: $LATEST_JSON" >> "$LOG_FILE"
        $PYTHON_BIN scripts/generate_daily_brief.py "$LATEST_JSON" >> "$LOG_FILE" 2>&1
        BRIEF_EXIT=$?
        if [ $BRIEF_EXIT -eq 0 ]; then
            echo "✅ Daily brief generated successfully" >> "$LOG_FILE"
        else
            echo "⚠️  Daily brief generation failed (exit code: $BRIEF_EXIT)" >> "$LOG_FILE"
        fi
    else
        echo "⚠️  No articles JSON found - skipping daily brief" >> "$LOG_FILE"
    fi
else
    echo "⚠️  Pipeline failed - skipping health check and daily brief" >> "$LOG_FILE"
fi

# Keep only last 30 days of logs
find logs/cron -name "pipeline_*.log" -mtime +30 -delete 2>/dev/null || true

exit $EXIT_CODE
