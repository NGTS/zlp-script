#!/usr/bin/env bash

set -e

if [[ $# -ne 1 ]]; then
    echo "Program usage: $0 <dir>" >&2
    exit 1
fi

BASEDIR=${PWD}
OUTPUTDIR=${BASEDIR}/testdata

setup() {
    echo "Setting up"
    rm -rf ${OUTPUTDIR}
    mkdir -p ${OUTPUTDIR}/OriginalData
    cp -r ${BASEDIR}/$1/images ${OUTPUTDIR}/OriginalData/
    echo "Setup complete"
}

perform_test() {
    local readonly sourcedir=$1
    sh ./ZLP_TestRun1_srw.sh ZLPTest ${OUTPUTDIR} ${BASEDIR}/$sourcedir/input-catalogue.fits ${BASEDIR}/$sourcedir/initial_wcs_solution.pickle ${sourcedir}/srw_confidence.fits ${sourcedir}/shuttermap.fits ${sourcedir}/catcache
}

test_photom_script() {
    PYTHONPATH=${BASEDIR}/scripts:$BASEDIR/scripts/NGTS_workpackage:$PYTHONPATH python \
        scripts/NGTS_workpackage/bin/ZLP_app_photom.py -h
}

main() {
    setup $1
    perform_test $1
}

main $@
