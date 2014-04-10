#!/bin/bash

set -o nounset
set -o errexit

WORKINGDIR=/ngts/pipedev
IMGDIRS=${WORKINGDIR}/OriginalData/images/201307[0-1][1,4,5]/*
RUNNAME="SimonTest1"

BIASLIST=${WORKINGDIR}/OriginalData/output/${RUNNAME}_bias.list
DARKLIST=${WORKINGDIR}/OriginalData/output/${RUNNAME}_dark.list
FLATLIST=${WORKINGDIR}/OriginalData/output/${RUNNAME}_flat.list
SHUTTERMAP=shuttermap.fits
CONFMAP=${WORKINGDIR}/InputCatalogue/srw_confidence.fits
CORES=8


T1="0" # create input lists
T2="0" # create masterbias
T3="0" # create masterdark
T4="0" # copy temporary shutter map
T5="0" # create masterflat
T6="0" # reduce dithered images
T7="0" # reduce science images
T8="0" # wait for jobs to finish
T9="0" # create input catalogues
T10="0" # perform photometry

T12="0" # run image subtraction
T13="0" # detrend


# Zero Level Pipeline
# Here all the commands are listed.
# this script can be run  from command line. to do the whole pipeline.


create_input_lists() {
    echo "Create lists with Images"
    ${WORKINGDIR}/OriginalData/scripts/createlists.py "$IMGDIRS" IMAGE fits $RUNNAME 
}

create_master_bias() {
    # Create MasterBias
    echo "Create MasterBias"
    CMD="`system_python` /home/ag367/progs/pipebias.py $BIASLIST ${RUNNAME}_MasterBias.fits ${WORKINGDIR}/Reduction/${RUNNAME}"
    submit_synchronous_job "${CMD}" "${RUNNAME}_BIAS"
}

create_master_dark() {
    #Create MasterDark
    echo "Create MasterDark"
    CMD="`system_python` /home/ag367/progs/pipedark.py $DARKLIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits ${WORKINGDIR}/Reduction/${RUNNAME}"
    submit_synchronous_job "${CMD}" "${RUNNAME}_DARK"
}

copy_temporary_shuttermap() {
    echo "Copying temporary shutter map"
    # # !!!! be carefull, shuttermap not yet automatically created. will be copied manualy
    # #
    DEST=${WORKINGDIR}/Reduction/${RUNNAME}
    ensure_directory "${DEST}"
    cp /home/ag367/test/shuttermap.fits "${DEST}/${SHUTTERMAP}"
}


create_master_flat() {
    #Create MasterFlat
    echo "Create MasterFlat"
    CMD="`system_python` /home/ag367/progs/pipeflat.py $FLATLIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits $SHUTTERMAP ${RUNNAME}_MasterFlat.fits ${WORKINGDIR}/Reduction/${RUNNAME}"
    submit_synchronous_job "${CMD}" "${RUNNAME}_FLAT"
}

reduce_images() {
    # Helper function to reduce a list of lists of images
    # Function submits jobs asynchronously and returns the list of job names
    #   used to run the analysis so the wait step can halt other processing.
    IMAGELISTS="${1}"
    JOBNAMES=""
    counter="0"
    for IMAGELIST in ${IMAGELISTS}
    do 
        IMAGELIST=${IMAGELIST#${WORKINGDIR}} 
        IMAGELIST=${IMAGELIST#/OriginalData/output/} 
        ensure_directory ${WORKINGDIR}/Reduction/${RUNNAME}/${IMAGELIST%.*}
        CMD="`system_python` /home/ag367/progs/pipered.py ${WORKINGDIR}/OriginalData/output/$IMAGELIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits $SHUTTERMAP ${RUNNAME}_MasterFlat.fits ${WORKINGDIR}/Reduction/${RUNNAME} ${WORKINGDIR}/Reduction/${RUNNAME}/${IMAGELIST%.*}"
        submit_asynchronous_job "${CMD}" "${IMAGELIST%.*}"
        if [ "$counter" -ne "0" ] ; then JOBNAMES=${JOBNAMES}"," ; fi 
        JOBNAMES=${JOBNAMES}${IMAGELIST%.*}
        counter="1"
    done
    echo $JOBNAMES
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

submit_synchronous_job() {
    CMD="${1}"
    JOBNAME="${2}"
    echo "${CMD}" | qsub -N "${JOBNAME}" -S /bin/bash -sync y -q parallel >/dev/null
}

submit_asynchronous_job() {
    CMD="${1}"
    JOBNAME="${2}"
    echo "${CMD}" | qsub -N "${JOBNAME}" -S /bin/bash -q parallel >/dev/null
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

# Do photometry on subtracted Images

main() {
    setup_environment

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

main
