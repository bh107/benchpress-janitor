#!/usr/bin/env bash
source config.sh

DATE=`date +%Y_%m_%d`
#SUITES="numpy_vs_bohrium"
SUITES="heat_equation leibnitz_pi rosenbrock numpy_vs_bohrium" 
#SUITES="leibnitz_pi heat_equation rosenbrock"

for SUITE in $SUITES
do
    echo "Adding ${SUITE} to watch" >> $PT_REPOS/janitor.log
    touch $PT_REPOS/workdir/watch/$SUITE
    echo "${DATE}-01" >> $PT_REPOS/workdir/watch/$SUITE
    echo "${DATE}-02" >> $PT_REPOS/workdir/watch/$SUITE
done
