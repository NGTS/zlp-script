#!/usr/bin/env bash
#$ -S /bin/bash -cwd -pe parallel 8 -N input-catalogue


set -e

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

copy_files() {
    OUTPUTDIR=$1
    cp metadata.sqlite catfile.fits catfile.ell outstack.fits outstackconf.fits stackfilelist ${OUTPUTDIR}
}

perform_analysis() {
    FILELIST=$1
    CONFIDENCE=$2
    OUTPUTDIR=$3
    PID=$$
    
    # Copy the source files onto local disk
    TMPDIR="ngts-${PID}"
    NEWFILELIST="filelist.txt"
    (cd /tmp
        test -d "${TMPDIR}" || mkdir "${TMPDIR}"
        (cd "/tmp/${TMPDIR}"
            echo "Copying files to `pwd`"
            cp `cat ${FILELIST} | cut -d ' ' -f 1` .
            find . -name '*.fits' | while read fname; do echo "$fname ok"; done > ${NEWFILELIST}

            time ZLP_create_cat.py --confmap ${CONFIDENCE} --filelist ${NEWFILELIST} --verbose --create-ell

            copy_files "${OUTPUTDIR}"
        )
        rm -rf "${TMPDIR}"
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
