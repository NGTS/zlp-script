#!/usr/bin/env bash

set -e

OUTPUTDIR=testdata

setup() {
    echo "Setting up"
    rm -rf ${OUTPUTDIR}
    mkdir -p ${OUTPUTDIR}/OriginalData
    cp -r source/images ${OUTPUTDIR}/OriginalData/
    echo "Setup complete"
}

perform_test() {
    sh ./ZLP_TestRun1_srw.sh ${OUTPUTDIR}
}

main() {
    setup
    perform_test
}

main
