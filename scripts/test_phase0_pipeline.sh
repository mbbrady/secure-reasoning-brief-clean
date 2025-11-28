#!/bin/bash
# Phase-0 Pipeline Test Script
# Runs a minimal pipeline execution to verify telemetry infrastructure

set -e  # Exit on error

echo "======================================"
echo "Phase-0 Telemetry Pipeline Test"
echo "======================================"
echo ""

# Change to project directory
cd "$(dirname "$0")/.."

# Clean up old data structure
echo "🧹 Cleaning old data structure..."
rm -rf data/research/agent_graph data/research/boundary_events 2>/dev/null || true

# Verify Python environment
echo "🐍 Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

# Check required packages
echo "📦 Checking required packages..."
python3 -c "import feedparser, requests, pandas" 2>/dev/null || {
    echo "❌ Missing required packages. Install with:"
    echo "   pip install -r requirements.txt"
    exit 1
}

# Run the fetcher with research logging enabled
echo ""
echo "🚀 Running fetch_and_summarize.py..."
echo "   (This will generate Phase-0 telemetry data)"
echo ""

# Set environment variables for minimal run
export RKL_LOGGING_ENABLED=true
export BRIEF_SUMMARY_MAX_WORDS=50  # Shorter summaries for test

# Run the script
python3 scripts/fetch_and_summarize.py

# Check if data was generated
echo ""
echo "🔍 Checking generated data..."

if [ ! -d "data/research" ]; then
    echo "❌ No data/research directory created"
    exit 1
fi

# Count artifacts
echo ""
echo "📊 Artifact counts:"
for artifact in execution_context reasoning_graph_edge boundary_event governance_ledger; do
    count=$(find "data/research/$artifact" -name "*.ndjson" -o -name "*.parquet" 2>/dev/null | wc -l)
    echo "   - $artifact: $count file(s)"
done

echo ""
echo "✅ Pipeline test complete!"
echo ""
echo "🧪 Running health check..."
echo ""

# Run health check
python3 scripts/health_check.py

exit $?
