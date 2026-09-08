#!/usr/bin/env bash

# run all metric scrips 
#
# Use:
#   cd courseProjectCode/Metrics
#   chmod +x run_all_metrics.sh (only first time)
#   ./run_all_metrics.sh

echo "lines of code"
python3 loc_metrics.py ../../searx
echo

echo "comment density"
python3 comment_density_metrics.py ../../searx
echo

echo "testability"
python3 testability_metrics.py ../..