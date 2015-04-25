#!/usr/bin/env bash
source config.sh

#
# Choke the output of pushd/popd
#
pushd () {
    command pushd "$@" > /dev/null
}

popd () {
    command popd "$@" > /dev/null
}

# Look here
DONEDIR="$PT_REPOS/workdir/done"
CONTAINERS=`ls $DONEDIR`

for CONTAINER in $CONTAINERS
do
    CONTAINER_PATH="$DONEDIR/$CONTAINER"
    TAR_PATH="$CONTAINER_PATH.tgz"
    TAR_NAME="$CONTAINER.tgz"

    # Not interested in empty, in something that has already been exported
    # or exporting exports :)
    if [[ "$CONTAINER" == "empty" || -e "$TAR_PATH" || -f "$CONTAINER_PATH" ]];
    then
        continue
    fi;
    echo "** Exporting $TAR_NAME" >> $PT_REPOS/janitor.log
    # Create the archive
    pushd $CONTAINER_PATH
    tar czf $TAR_NAME *
    mv $TAR_NAME ..
    popd
    # Ship it off
    echo "put $TAR_PATH" | sftp $SFTP_HOST:$SFTP_TARGET
done;
