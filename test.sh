#!/usr/bin/env bash

set -e

abspath() {
    python -c "import os; print os.path.realpath('${1}')"
}

if [[ $# -ne 1 ]]; then
    echo "Program usage: $0 <dir>" >&2
    exit 1
fi

BASEDIR=$(abspath $(dirname $0))
OUTPUTDIR=${BASEDIR}/testdata

# Remove this to test with sysrem
export NOSYSREM=true

setup() {
    echo "Setting up"
    rm -rf ${OUTPUTDIR}
    mkdir -p ${OUTPUTDIR}/OriginalData
    cp -r $1/images ${OUTPUTDIR}/OriginalData/
    echo "Setup complete"

    # Use whichever python is available
    export DISABLE_ANACONDA=1
}

perform_test() {
    local readonly sourcedir=$(abspath $1)
    if [ -f ${sourcedir}/initial_wcs_solution.pickle ]; then
        solution_filename=${sourcedir}/initial_wcs_solution.pickle
    else
        solution_filename=${sourcedir}/wcs_solution.json
    fi
    echo "Solution file ${solution_filename}"
    TESTQA=true bash ./ZLP_pipeline.sh ZLPTest ${OUTPUTDIR} ${sourcedir}/input-catalogue.fits ${solution_filename} ${sourcedir}/srw_confidence.fits ${sourcedir}/shuttermap.fits ${sourcedir}/wcs-reference-frame.fits
}

test_photom_script() {
    PYTHONPATH=${BASEDIR}/scripts:$BASEDIR/scripts/zlp-photometry:$PYTHONPATH python \
        scripts/zlp-photometry/bin/ZLP_app_photom.py -h
}

verify() {
    echo Verifying
    verify_in_mjd_order
    verify_psf_info
    verify_casu_detrending_zero_point
    verify_pipeline_sha_present_in_output_file
    if [ -z ${NOSYSREM:-} ]; then
        verify_post_tamuz_present
    fi
}

verify_in_mjd_order() {
    echo Verifying MJD order
    python ${BASEDIR}/testing/ensure_in_mjd_order.py $(find ${OUTPUTDIR} -name 'output.fits')
    if [ "$?" != "0" ]; then
        echo "ERROR: failure in validation 'mjd order'" >&2
        exit "$?"
    fi
}

verify_psf_info() {
    echo "Verifying psf info"
    FNAME=$(find ${OUTPUTDIR} -name 'output.fits')
    python ${BASEDIR}/testing/ensure_psf_info.py ${FNAME}
}

verify_casu_detrending_zero_point() {
    echo "Verifying CASU zero point"
    FNAME=$(find ${OUTPUTDIR} -name 'casu-lightcurves-out.fits')
    python ${BASEDIR}/testing/ensure_casu_zero_point.py ${FNAME}
}

verify_pipeline_sha_present_in_output_file() {
    echo "Verifying pipeline SHA is present in output file"
    FNAME=$(find ${OUTPUTDIR} -name 'output.fits')
    python ${BASEDIR}/testing/ensure_pipeline_sha.py ${FNAME}
}

verify_post_tamuz_present() {
    echo "Verifying post tamuz flux is present in the output file"
    FNAME=$(find ${OUTPUTDIR} -name 'output.fits')
    python ${BASEDIR}/testing/ensure_tamflux.py ${FNAME}
}

main() {
    setup $1
    perform_test $1
    verify
    echo "Finished"
}

main $@
