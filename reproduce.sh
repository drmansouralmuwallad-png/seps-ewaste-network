#!/bin/sh
# One command from inputs to results: solve everything, then regenerate the numbers,
# supplementary tables and figures used in the article.
set -e
./run_all.sh
python3 make_numbers.py
python3 make_supplement.py
mkdir -p figures
python3 make_fig1.py; python3 make_map.py; python3 make_figures.py
echo "Done: numbers.json/numbers.tex, supp_tables.tex and figures/ regenerated."
