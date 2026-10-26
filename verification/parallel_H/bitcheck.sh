#!/bin/bash
# bit-identity of two runs: every file of every time folder (except uniform/ time stamps)
A=$1; B=$2
nf=0; nd=0
for t in $(cd "$A" && ls -d [0-9]* | grep -v '^0$'); do
  for f in $(cd "$A/$t" && find . -type f ! -path './uniform/*'); do
    nf=$((nf+1))
    cmp -s "$A/$t/$f" "$B/$t/$f" || { nd=$((nd+1)); [ $nd -le 5 ] && echo "differs: $t/$f"; }
  done
done
echo "files compared: $nf, different: $nd"
cmp -s "$A/waterBudget.csv" "$B/waterBudget.csv" && echo "waterBudget.csv identical" || echo "waterBudget.csv differs"
