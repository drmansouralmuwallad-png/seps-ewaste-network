#!/bin/sh
# Regenerates every result file, in order (about 4-5 hours on two cores; the joint model
# alone takes about 2 hours). Scripts resume from existing result files, so a fresh run
# first removes them; set RESUME=1 to keep them and continue an interrupted run.
set -e
mkdir -p logs
if [ "${RESUME:-0}" != "1" ]; then
  rm -f stage1.json stage1_solve_log.json results.json extra.json mc_rows.jsonl mc_retry_*.jsonl \
        diag_mc.json lowvol.json radius.json equity_enum.json tied_maxprofit.json equity_regional.json \
        joint.json joint_sites.json recovery.json caputil.json employment.json lr_sweep.json lr_solve_log.json \
        model_sizes.json
  rm -rf bench
fi
python3 make_generation.py    > logs/generation.log 2>&1
python3 stage1.py             > logs/stage1.log 2>&1
python3 make_params.py        > logs/params.log 2>&1
python3 run_core.py           > logs/core.log 2>&1
python3 run_extra.py          > logs/extra.log 2>&1
python3 run_mc.py 0 2         > logs/mc0.log 2>&1 &
python3 run_mc.py 1 2         > logs/mc1.log 2>&1
wait
python3 run_mc.py retry 0 2  > logs/mc_retry0.log 2>&1 &
python3 run_mc.py retry 1 2  > logs/mc_retry1.log 2>&1
wait
python3 run_mc.py collect     > logs/mc.log 2>&1
python3 run_lr.py             > logs/lr.log 2>&1
python3 equity_lp.py          > logs/equity.log 2>&1
python3 run_tied_maxprofit.py > logs/tied_maxprofit.log 2>&1
python3 run_equity_regional.py > logs/equity_regional.log 2>&1
python3 run_radius.py         > logs/radius.log 2>&1
python3 run_joint.py          > logs/joint.log 2>&1
python3 run_joint_sites.py    > logs/joint_sites.log 2>&1
python3 model_sizes.py        > logs/model_sizes.log 2>&1
python3 diag_mc.py           > logs/diag_mc.log 2>&1
python3 run_recovery.py       > logs/recovery.log 2>&1
python3 run_caputil.py        > logs/caputil.log 2>&1
python3 run_lowvol.py         > logs/lowvol.log 2>&1
python3 run_employment.py     > logs/employment.log 2>&1
./run_bench.sh
echo done > logs/ALL_DONE
