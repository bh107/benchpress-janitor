#!/usr/bin/env bash
source config.sh

echo "01" > $PT_REPOS/workdir/watch/perftest_mini
echo "02" > $PT_REPOS/workdir/watch/perftest_mini

./janitor.py ~/bohrium watch 
./janitor.py ~/bohrium run
./janitor.py ~/bohrium graph

less +F janitor.log

