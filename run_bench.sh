#!/bin/sh
# Benchmark transport cost (Section 5.1): re-run the core experiments, the equity
# enumeration and the radius check with TRANSPORT=benchmark, in bench/.
set -e
rm -rf bench; mkdir -p bench/logs
cp model.py stage1.py run_core.py equity_lp.py run_radius.py realdata.json stage1.json bench/
cd bench
# recovery mandates are not part of the benchmark; pre-mark them so run_core.py skips them
echo '{"recovery": [{"skipped": "not needed for the transport benchmark"}]}' > results.json
TRANSPORT=benchmark python3 run_core.py   > logs/core.log 2>&1
TRANSPORT=benchmark python3 equity_lp.py  > logs/equity.log 2>&1
TRANSPORT=benchmark python3 run_radius.py > logs/radius.log 2>&1
echo done > logs/BENCH_DONE
