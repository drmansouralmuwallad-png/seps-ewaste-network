# Public e-waste recovery network for Saudi Arabia: code and data

Code and data for the article

> Almuwallad, M. *Planning a public e-waste recovery network for profit, jobs and regional
> equity: a two-stage compromise model applied to Saudi Arabia.* Submitted to
> *Socio-Economic Planning Sciences*.

The repository regenerates every number, table and figure in the article and its
supplementary material from the input data. The manuscript text itself is not included.

## The model in brief

- **Stage 1** (`stage1.py`) sites collection and segregation centres among 24 Saudi cities
  by set covering, with capacitated assignment, an aggregate spare-capacity (one-out) rule,
  a regional equity rule and a distance tie-break. It is solved with CBC.
- **Stage 2** (`model.py`) plans six periods of flows to recycling, refurbishing and disposal
  under workforce learning. It balances operating profit, operational utilisation (share of
  facility-period slots in operation) and employment (worker-periods) with a two-phase fuzzy
  max–min compromise. It is solved with HiGHS.
- **Experiments** (`run_*.py`): weighted-sum and ε-constraint benchmarks, sensitivity,
  recovery mandates, workforce learning, single-facility loss, Monte Carlo on generation,
  equal-cost alternative sitings, regional employment, a joint siting model, capacity
  utilisation, and a transport-cost benchmark (`bench/`).

## Quick start

```bash
pip install -r requirements.txt     # Python 3.13; PuLP 2.9.0 bundles CBC 2.10.3, highspy provides HiGHS 1.15.1
./reproduce.sh                      # solve everything, then regenerate numbers, tables and figures
```

`reproduce.sh` runs:

| Step | Command | Output |
|---|---|---|
| Solve every experiment, about 4–5 h on two cores (the joint model alone takes about 2 h) | `./run_all.sh` | result `.json` files, `logs/`, `bench/` |
| Every number quoted in the article | `python3 make_numbers.py` | `numbers.json`, `numbers.tex` |
| Every supplementary table | `python3 make_supplement.py` | `supp_tables.tex` |
| Figures 1–4 | `python3 make_fig1.py; python3 make_map.py; python3 make_figures.py` | `figures/` |

The result files of the reported runs are already included, so the last three steps can be
run on their own in seconds.

## Reproducibility

The reported runs used Python 3.13.16, PuLP 2.9.0, HiGHS 1.15.1 and CBC 2.10.3 on an Intel
Xeon @ 2.10 GHz with 2 logical CPUs and 7.8 GiB RAM (Linux). Solver settings were one thread,
relative MIP gap 10⁻⁴ and a 300 s limit per subproblem, with a 3,600 s retry and 3,600 s per
joint-model solve. Every solve's status and time is stored in the `solve_log` field of the
result file it belongs to; `compstats.py` summarises them.

A clean re-run from the inputs on a different machine reproduced every result file exactly.
That includes the 120 Monte Carlo draws, the time-limited joint-model solves and the
benchmark. Only solve times differed.

## Files

`DATA.md` documents every input and output file. The main ones:

| File | Content |
|---|---|
| `population.json` | Saudi Census 2022 governorate populations of the 24 nodes, with the source of each figure |
| `realdata_original.json` | The original study data (city names, 24 × 6 generation matrix, road distances) |
| `realdata.json` | Collection volumes allocated by population (from `make_generation.py`) and road distances used by the model |
| `params_complete.json` | Every model parameter with its value, class and source |
| `results.json`, `stage1.json`, … | Solver output of the reported runs |

## Licence

- Code (`.py`, `.sh`): MIT — see `LICENSE`.
- Data (`.json`, `.jsonl`): CC BY 4.0 — see `LICENSE-DATA`.

## Citation

See `CITATION.cff`, or use GitHub's "Cite this repository" button. Please cite the article
once it is published.
