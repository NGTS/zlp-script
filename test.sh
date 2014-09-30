#!/usr/bin/env bash

abspath() {
    python -c "import os; print os.path.realpath('${1}')"
}

set -e

if [[ $# -ne 1 ]]; then
    echo "Program usage: $0 <dir>" >&2
    exit 1
fi

BASEDIR=$(abspath $(dirname $0))
OUTPUTDIR=${BASEDIR}/testdata


setup() {
    echo "Setting up"
    rm -rf ${OUTPUTDIR}
    mkdir -p ${OUTPUTDIR}/OriginalData
    cp -r ${BASEDIR}/$1/images ${OUTPUTDIR}/OriginalData/
    echo "Setup complete"
}

perform_test() {
    local readonly sourcedir=$(abspath $1)
    sh ./ZLP_pipeline.sh ZLPTest ${OUTPUTDIR} $sourcedir/input-catalogue.fits $sourcedir/initial_wcs_solution.pickle ${sourcedir}/srw_confidence.fits ${sourcedir}/shuttermap.fits ${sourcedir}/wcs-reference-frame.fits
}

test_photom_script() {
    PYTHONPATH=${BASEDIR}/scripts:$BASEDIR/scripts/zlp-photometry:$PYTHONPATH python \
        scripts/zlp-photometry/bin/ZLP_app_photom.py -h
}

verify() {
    echo Verifying
    verify_in_mjd_order
}

verify_in_mjd_order() {
    echo Verifying MJD order
    python ${BASEDIR}/testing/ensure_in_mjd_order.py $(find ${OUTPUTDIR} -name 'output.fits')
    if [ "$?" != "0" ]; then
        echo "ERROR: failure in validation 'mjd order'" >&2
        exit "$?"
    fi
}

main() {
    setup $1
    perform_test $1
    verify
    echo "Finished"
}

main $@
