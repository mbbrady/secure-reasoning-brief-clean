#!/bin/bash
# Wrapper script for weekly blog generation - runs Monday 10 AM

# Set PATH to include common locations
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin:$PATH"

# Change to project directory
cd "$(dirname "$0")/.."

# Activate conda environment (rkl-briefs)
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
LOG_FILE="logs/cron/weekly_blog_$TIMESTAMP.log"

echo "=========================================" >> "$LOG_FILE"
echo "Weekly Blog Generation: $TIMESTAMP" >> "$LOG_FILE"
echo "=========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Debug: Show which python we're using
echo "Python: $PYTHON_BIN" >> "$LOG_FILE"
echo "Conda env: $CONDA_DEFAULT_ENV" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Run weekly blog generation with output captured
$PYTHON_BIN scripts/generate_weekly_blog.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "" >> "$LOG_FILE"
echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"

# Keep only last 30 days of logs
find logs/cron -name "weekly_blog_*.log" -mtime +30 -delete 2>/dev/null || true

exit $EXIT_CODE
