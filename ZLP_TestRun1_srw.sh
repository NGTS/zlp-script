#!/usr/bin/env bash

set -o nounset
set -o errexit
set -o pipefail

if [[ $# -ne 4 ]]; then
    echo "Usage: $0 <runname> <root_directory> <input-catalogue> <initial-wcs-solution>" >&2
    exit 1
fi

# command line arguments
readonly BASEDIR=$(readlink -f $(dirname $0))
readonly RUNNAME=${1}
readonly WORKINGDIR=$(readlink -f ${2})
readonly GIVEN_INPUTCATALOGUE=$3
readonly WCSSOLUTION=$4

readonly IMGDIRS=${WORKINGDIR}/OriginalData/images/**/*
readonly SCRIPTDIR=${BASEDIR}/scripts

readonly BIASLIST=${WORKINGDIR}/OriginalData/output/${RUNNAME}_bias.list
readonly DARKLIST=${WORKINGDIR}/OriginalData/output/${RUNNAME}_dark.list
readonly FLATLIST=${WORKINGDIR}/OriginalData/output/${RUNNAME}_flat.list
readonly SHUTTERMAP=shuttermap.fits
readonly CONFMAP=${WORKINGDIR}/InputCatalogue/srw_confidence.fits
readonly CORES=12


readonly T1="1" # create input lists
readonly T2="1" # create masterbias
readonly T3="1" # create masterdark
readonly T4="1" # copy temporary shutter map
readonly T5="1" # create masterflat
readonly T6="0" # reduce dithered images
readonly T7="1" # reduce science images
readonly T8="0" # wait for jobs to finish
readonly T9="0" # create input catalogues
readonly T10="0" # perform photometry

readonly T12="0" # run image subtraction
readonly T13="0" # detrend


# Zero Level Pipeline
# Here all the commands are listed.
# this script can be run  from command line. to do the whole pipeline.


create_input_lists() {
    echo "Create lists with Images"
    CMD="${SCRIPTDIR}/createlists.py \"$IMGDIRS\" IMAGE fits $RUNNAME"
    echo $CMD
    ${CMD}
}

create_master_bias() {
    # Create MasterBias
    echo "Create MasterBias"
    CMD="`system_python` ${SCRIPTDIR}/pipebias.py $BIASLIST ${RUNNAME}_MasterBias.fits ${WORKINGDIR}/Reduction/output/${RUNNAME}"
    ${CMD}
}

create_master_dark() {
    #Create MasterDark
    echo "Create MasterDark"
    CMD="`system_python` ${SCRIPTDIR}/pipedark.py $DARKLIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits ${WORKINGDIR}/Reduction/output/${RUNNAME}"
    ${CMD}
}

copy_temporary_shuttermap() {
    echo "Copying temporary shutter map"
    # # !!!! be carefull, shuttermap not yet automatically created. will be copied manualy
    # #
    DEST=${WORKINGDIR}/Reduction/output/${RUNNAME}
    ensure_directory "${DEST}"
    cp /home/ag367/test/shuttermap.fits "${DEST}/${SHUTTERMAP}"
}


create_master_flat() {
    #Create MasterFlat
    echo "Create MasterFlat"
    CMD="`system_python` ${SCRIPTDIR}/pipeflat.py $FLATLIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits $SHUTTERMAP ${RUNNAME}_MasterFlat.fits ${WORKINGDIR}/Reduction/output/${RUNNAME}"
    ${CMD}
}

reduce_images() {
    # Helper function to reduce a list of lists of images
    # Function submits jobs asynchronously and returns the list of job names
    #   used to run the analysis so the wait step can halt other processing.
    IMAGELISTS="${1}"
    counter="0"
    for IMAGELIST in ${IMAGELISTS}
    do 
        IMAGELIST=${IMAGELIST#${WORKINGDIR}} 
        IMAGELIST=${IMAGELIST#/OriginalData/output/} 
        ensure_directory ${WORKINGDIR}/Reduction/output/${RUNNAME}/${IMAGELIST%.*}
        CMD="`system_python` ${SCRIPTDIR}/pipered.py ${WORKINGDIR}/OriginalData/output/$IMAGELIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits $SHUTTERMAP ${RUNNAME}_MasterFlat.fits ${WORKINGDIR}/Reduction/output/${RUNNAME} ${WORKINGDIR}/Reduction/output/${RUNNAME}/${IMAGELIST%.*}"
        ${CMD}
    done
}

reduce_dithered_images() {
    echo "Reduce Dithered Images"
    IMAGELISTS=${WORKINGDIR}/OriginalData/output/${RUNNAME}_dither_*.list
    DITHJOBS=`reduce_images "${IMAGELISTS}"`
}

reduce_science_images() {
    echo "Reduce Science Images"
    IMAGELISTS=$WORKINGDIR/OriginalData/output/${RUNNAME}_image_*.list
    IMGJOBS=`reduce_images "${IMAGELISTS}"`
}

wait_for_jobs() {
    if [ -z "$1" ]
    then
        echo "Error in invokation; wait_for_jobs <jobids>" >&2
        exit 1
    fi

    JOBIDS="${1}"

    echo "Wait until jobs '${JOBIDS}' finish"
    qsub -hold_jid "${JOBIDS}" -N WAIT  -sync y -cwd ${WORKINGDIR}/wait.sh 
}


create_input_catalogue() {
    # Frame Selection / Quality and Integrity Check

    # Create Input Catalogue if not already exists for imagelists
    cd ${WORKINGDIR}/InputCatalogue
    local JOBLIST=""
    for DITHERFILE in ${WORKINGDIR}/OriginalData/output/${RUNNAME}_dither_*.list
    do 
        DITHERFILE=${DITHERFILE#${WORKINGDIR}}
        DITHERFILE=${DITHERFILE#/OriginalData/output/}
        JOBNAME=${DITHERFILE%.*}

        OUTPUTDIR=${WORKINGDIR}/InputCatalogue/output/${RUNNAME}/${JOBNAME}
        ensure_directory "${OUTPUTDIR}"
        find ${WORKINGDIR}/Reduction/${RUNNAME}/${JOBNAME} -name '*.fits' > ${WORKINGDIR}/InputCatalogue/${JOBNAME}.txt
        echo "${WORKINGDIR}/InputCatalogue/run_on_directory.sh ./${JOBNAME}.txt ${CONFMAP} ./output/${RUNNAME}"
        qsub -N ${JOBNAME} ${WORKINGDIR}/InputCatalogue/run_on_directory.sh ./${JOBNAME}.txt ${CONFMAP} ${OUTPUTDIR}
        JOBLIST="${JOBLIST} ${JOBNAME}"
    done
    JOBLIST=`echo ${JOBLIST} | sed 's/ /,/g'`
    cd ${WORKINGDIR}

    wait_for_jobs "${JOBLIST}"
}

perform_aperture_photometry() {
    echo "Running aperture photometry"
    cd ${WORKINGDIR}/AperturePhot
    local JOBLIST=""
    for FILELIST in ${WORKINGDIR}/OriginalData/output/${RUNNAME}_image_*.list
    do
        FILELIST=${FILELIST#${WORKINGDIR}}
        FILELIST=${FILELIST#/OriginalData/output/}
        JOBNAME=${FILELIST%.*}
        OUTPUTDIR=${WORKINGDIR}/AperturePhot/output/${RUNNAME}/${JOBNAME}
        IMAGEFILELIST=${OUTPUTDIR}/filelist.txt
        DITHERJOB=`echo $JOBNAME | sed 's/image/dither/'`
        CATFILE=${WORKINGDIR}/InputCatalogue/output/${RUNNAME}/${DITHERJOB}/catfile.fits
        if [ -f ${CATFILE} ]
        then
            echo "Found catalogue ${CATFILE}"
            ensure_directory "${OUTPUTDIR}"

            # XXX Temporary measure to speed up analysis, only run on the first 100 images
            # find ${WORKINGDIR}/Reduction/${RUNNAME}/${JOBNAME} -name '*.fits' | head -n 100 > ${IMAGEFILELIST}

            find ${WORKINGDIR}/Reduction/${RUNNAME}/${JOBNAME} -name '*.fits' > ${IMAGEFILELIST}
            # TODO: Needs CATPATH
            echo "${WORKINGDIR}/AperturePhot/run_app_photom.sh ${IMAGEFILELIST} ${CONFMAP} ${CATFILE} ${OUTPUTDIR}"
            qsub -N ${JOBNAME} -S /bin/bash -cwd ${WORKINGDIR}/AperturePhot/run_app_photom.sh ${IMAGEFILELIST} ${CONFMAP} ${CATFILE} ${OUTPUTDIR}

            JOBLIST="${JOBLIST} ${JOBNAME}"
        fi

    done
    JOBLIST=`echo ${JOBLIST} | sed 's/ /,/g'`
    cd ${WORKINGDIR}
    wait_for_jobs "${JOBLIST}"
}

run_detrending() {
    echo "Detrending with SYSREM"
    OUTPUTDIR="${WORKINGDIR}/Detrending/output/${RUNNAME}"
    # Old incorrect version of sysrem
    # SYSREM=${WORKINGDIR}/Detrending/tamuz_src/sysrem

    SYSREM=/wasp/home/sw/SelectionEffects/bin/Sysrem.srw

    PHOTOMOUT_FILES=`find ${WORKINGDIR}/AperturePhot/output/${RUNNAME} -name 'output.fits'`
    for PHOTOMOUT in $PHOTOMOUT_FILES
    do
        # Take the last two path elements
        JOBNAME=`echo $PHOTOMOUT | rev | cut -d '/' -f 2 | rev`
        OUTSUBDIR=${OUTPUTDIR}/${JOBNAME}
        ensure_directory ${OUTSUBDIR}
        OUTFILE=${OUTSUBDIR}/tamout.fits
        CMD="${SYSREM} ${PHOTOMOUT} -o ${OUTFILE}"
        echo ${CMD}
        qsub -b y -pe parallel 24 ${SYSREM} ${PHOTOMOUT} -o ${OUTFILE}
    done
}


# if [ "$T11" = "1" ] ; then
#  # Subtract Images
#  echo "Subtract Science Images"
#   cd /ngts/pipedev/Subtractphot
#   for IMAGEFILE in $WORKINGDIR/OriginalData/output/${RUNNAME}_image_*.list
#   do
#     IMAGEFILE=${IMAGEFILE#${WORKINGDIR}}
#     IMAGEFILE=${IMAGEFILE#/OriginalData/output/}
#     IMAGEFILE=${IMAGEFILE%.*}
#     echo $IMAGEFILE
#     $IMFILE = ${IMAGEFILE#${RUNNAME}_image_}
#     numsfiles=($WORKINGDIR/InputCatalogue/output/*/*${IMFILE}/outstack.fits)
#     numfiles=${#numfiles[@]}
#     if [ "$numfiles" > "1" ] ; then
# 	echo "${numfiles} reference Frames found, selecting the first: ${numsfiles[0]}"
#     fi
#     $Reference =  ${numsfiles[0]}
#     $RefCat = ($WORKINGDIR/InputCatalogue/output/*/*${IMFILE}/catfile.fits)
#     $RefCat = ${RefCat[0]}
#     find  ${WORKINGDIR}/Reduction/${RUNNAME}/${IMAGEFILE} -name '*.fits' > ${WORKINGDIR}/Subtractphot/${IMAGEFILE}.txt
#     python /ngts/pipedev/Subtractphot/scripts/image_subtraction_main.py /ngts/pipedev/Subtractphot $Reference ${WORKINGDIR}/Subtractphot/${IMAGEFILE}.txt ${RefCat} 5 20 ${RUNNAME}
#   done
#   cd /ngts/pipedev
# fi

# Some helper functions
ensure_directory() {
    DIR=${1}
    test -d ${DIR} || mkdir -p ${DIR}
}

setup_environment() {
    echo "Environment set up"
    # BASEPATH=/ngts/pipedev/InputCatalogue
    # source ${BASEPATH}/venv/bin/activate
    # export PATH=/usr/local/casutools/bin:${PATH}
    # export LD_LIBRARY_PATH=/usr/local/wcslib/lib:/usr/local/cfitsio/lib:${LD_LIBRARY_PATH}

}

system_python() {
    echo "/usr/local/python/bin/python"
}

setup_directory_structure() {
    for subdir in OriginalData/output AperturePhot Reduction Reduction/output; do
        local dirpath=${WORKINGDIR}/${subdir}
        ensure_directory ${WORKINGDIR}/${subdir}
    done
}

# Do photometry on subtracted Images

main() {
    setup_environment
    setup_directory_structure

    cd ${WORKINGDIR}/OriginalData 
    [ "$T1" = "1" ] && create_input_lists

    cd ${WORKINGDIR}/Reduction
    [ "$T2" = "1" ] && create_master_bias 

    [ "$T3" = "1" ] && create_master_dark 

    [ "$T4" = "1" ] && copy_temporary_shuttermap

    [ "$T5" = "1" ] && create_master_flat 

    [ "$T6" = "1" ]&&  reduce_dithered_images 

    [ "$T7" = "1" ] && reduce_science_images 

    [ "$T8" = "1" ] && wait_for_jobs "${DITHJOBS}${IMGJOBS}"

    cd ${WORKINGDIR}
    [ "$T9" = "1" ] && create_input_catalogue 

    [ "$T10" = "1" ] && perform_aperture_photometry 

    [ "$T13" = "1" ] && run_detrending 
}

main 2>&1 | tee zlp.log
