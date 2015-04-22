#!/usr/bin/env bash
source config.sh

./janitor.py $BH_REPOS watch
./janitor.py $BH_REPOS run
./janitor.py $BH_REPOS postprocess
./export.sh
