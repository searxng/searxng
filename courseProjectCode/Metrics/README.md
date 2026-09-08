## How to run

get into the metrics folder:
```bash
cd courseProjectCode/Metrics 
```

run each one individually:
```bash
python3 loc_metrics.py ../../searx
python3 comment_density_metrics.py ../../searx
python3 testability_metrics.py ../..
```

run them all together: 
```bash
./run_all_metrics.sh
```