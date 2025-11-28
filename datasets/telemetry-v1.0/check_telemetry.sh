#!/bin/bash

echo "=== TELEMETRY DATA SUMMARY ==="
echo ""
echo "Total dataset size: $(du -sh /home/mike/project/rkl-consolidated/secure-reasoning-brief/datasets/telemetry-v1.0 | cut -f1)"
echo ""
echo "Files by category:"
for dir in boundary_event execution_context governance_ledger hallucination_matrix quality_trajectories reasoning_graph_edge retrieval_provenance secure_reasoning_trace system_state; do
  count=$(find /home/mike/project/rkl-consolidated/secure-reasoning-brief/datasets/telemetry-v1.0/telemetry_data/$dir -type f | wc -l)
  size=$(du -sh /home/mike/project/rkl-consolidated/secure-reasoning-brief/datasets/telemetry-v1.0/telemetry_data/$dir | cut -f1)
  echo "  $dir: $count files ($size)"
done
echo ""
echo "Total parquet files: $(find /home/mike/project/rkl-consolidated/secure-reasoning-brief/datasets/telemetry-v1.0/telemetry_data/ -name '*.parquet' | wc -l)"
echo "Total ndjson files: $(find /home/mike/project/rkl-consolidated/secure-reasoning-brief/datasets/telemetry-v1.0/telemetry_data/ -name '*.ndjson' | wc -l)"
echo ""
echo "Manifest files:"
ls /home/mike/project/rkl-consolidated/secure-reasoning-brief/datasets/telemetry-v1.0/telemetry_data/manifests/
