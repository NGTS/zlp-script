#!/usr/bin/env bash
#$ -S /bin/bash -cwd -pe parallel 24 -N input-catalogue

set -e

# Ensure this matches half of the invokation line above
NPROC=12


abspath() {
    readlink -f $1
}

validate_input() {
    if [[ "$#" != 3 ]]; then
        echo "Usage: `basename $0` <filelist> <confidence> <outputdir>" >&2
        exit 1
    fi
}

setup_environment() {
    BASEPATH=/ngts/pipedev/InputCatalogue
    source ${BASEPATH}/venv/bin/activate
    export PATH=/usr/local/casutools/bin:${PATH}
    export LD_LIBRARY_PATH=/usr/local/wcslib/lib:/usr/local/cfitsio/lib:${LD_LIBRARY_PATH}
}

perform_analysis() {
    FILELIST=$1
    CONFIDENCE=$2
    OUTPUTDIR=$3
    PID=$$

    (cd ${OUTPUTDIR}
    time ZLP_create_cat.py --confmap ${CONFIDENCE} --filelist ${FILELIST} --verbose --nproc ${NPROC}
    )
}

main() {
    validate_input $*
    setup_environment

    FILELIST=`abspath $1`
    CONFIDENCE=`abspath $2`
    OUTPUTDIR=`abspath $3`

    echo "Reading files from ${FILELIST}"
    echo "Using confidence map ${CONFIDENCE}"
    echo "Rendering to output directory ${OUTPUTDIR}"

    test -d ${OUTPUTDIR} || mkdir ${OUTPUTDIR}
    (cd ${OUTPUTDIR} && perform_analysis ${FILELIST} ${CONFIDENCE} ${OUTPUTDIR})
}

main $*
