#!/usr/bin/env bash
source config.sh

DATE=`date +%Y_%m_%d`
SUITES="engine heat_equation numpy_vs_bohrium"
#SUITES="heat_equation leibnitz_pi rosenbrock numpy_vs_bohrium" 
#SUITES="engine heat_equation leibnitz_pi rosenbrock" 
#SUITES="leibnitz_pi heat_equation rosenbrock"

for SUITE in $SUITES
do
    echo "** Adding ${SUITE} to watch" >> $PT_REPOS/janitor.log
    touch $PT_REPOS/workdir/watch/$SUITE
    echo "${DATE}" >> $PT_REPOS/workdir/watch/$SUITE
    #echo "01" >> $PT_REPOS/workdir/watch/$SUITE
    #echo "02" >> $PT_REPOS/workdir/watch/$SUITE
done
