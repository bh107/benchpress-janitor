#!/usr/bin/env bash
source config.sh

for SUITE in $SUITES
do
    DATE=`date +%Y_%m_%d`
    touch $PT_REPOS/workdir/watch/$SUITE
    echo "${DATE}-01" >> $PT_REPOS/workdir/watch/$SUITE
    echo "${DATE}-02" >> $PT_REPOS/workdir/watch/$SUITE
done
