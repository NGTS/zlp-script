#!/usr/bin/env bash

set -e

BASEDIR=${PWD}
OUTPUTDIR=${BASEDIR}/testdata

setup() {
    echo "Setting up"
    rm -rf ${OUTPUTDIR}
    mkdir -p ${OUTPUTDIR}/OriginalData
    cp -r ${BASEDIR}/source/images ${OUTPUTDIR}/OriginalData/
    echo "Setup complete"
}

perform_test() {
    sh ./ZLP_TestRun1_srw.sh ZLPTest ${OUTPUTDIR} ${BASEDIR}/source/input-catalogue.fits ${BASEDIR}/source/initial_wcs_solution.pickle
}

test_photom_script() {
    PYTHONPATH=${BASEDIR}/scripts:$BASEDIR/scripts/NGTS_workpackage:$PYTHONPATH python \
        scripts/NGTS_workpackage/bin/ZLP_app_photom.py -h
}

main() {
    setup
    perform_test
}

main
