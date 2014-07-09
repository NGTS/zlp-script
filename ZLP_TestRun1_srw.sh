#!/usr/bin/env bash

set -o nounset
set -o errexit
set -o pipefail

if [[ $# -ne 4 ]]; then
    cat >&2 <<-EOF
  Usage: $0 <runname> <root-directory> <input-catalogue> <initial-wcs-solution>

  Argument descriptions:

  * runname

  The name of the run to use. This is so multiple runs can be performed on different
  data, and the outputs can be unique.

  * root-directory

  This is the location of the input files. The directory structure must be as follows:

  root-directory
      OriginalData
          images
              <one directory per date>
                  action<number>_<optional description>
                      IMAGE*.fits

  * input-catalogue

  The list of coordinates to place apertures at

  * initial_wcs_solution

  The initial wcs solution computed by Tom's MCMC code to compute distortion
  parameters
EOF
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
readonly CONFMAP=${BASEDIR}/source/srw_confidence.fits
readonly CORES=2
readonly WCSREFCATALOGUE=${BASEDIR}/source/refcat.fits


readonly T1="1" # create input lists
readonly T2="1" # create masterbias
readonly T3="1" # create masterdark
readonly T4="1" # copy temporary shutter map
readonly T5="1" # create masterflat
readonly T6="0" # reduce dithered images
readonly T7="1" # reduce science images
readonly T8="0" # wait for jobs to finish
readonly T9="0" # create input catalogues
readonly T10="1" # perform photometry

readonly T12="0" # run image subtraction
readonly T13="0" # detrend


# Zero Level Pipeline
# Here all the commands are listed.
# this script can be run  from command line. to do the whole pipeline.


create_input_lists() {
    echo "Create lists with Images"
    CMD="python ${SCRIPTDIR}/createlists.py \"$IMGDIRS\" IMAGE fits $RUNNAME"
    echo $CMD
    ${CMD}
}

create_master_bias() {
    # Create MasterBias
    echo "Create MasterBias"
    CMD="python ${SCRIPTDIR}/pipebias.py $BIASLIST ${RUNNAME}_MasterBias.fits ${WORKINGDIR}/Reduction/output/${RUNNAME}"
    ${CMD}
}

create_master_dark() {
    #Create MasterDark
    echo "Create MasterDark"
    CMD="python ${SCRIPTDIR}/pipedark.py $DARKLIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits ${WORKINGDIR}/Reduction/output/${RUNNAME}"
    ${CMD}
}

copy_temporary_shuttermap() {
    echo "Copying temporary shutter map"
    # # !!!! be carefull, shuttermap not yet automatically created. will be copied manualy
    # #
    DEST=${WORKINGDIR}/Reduction/output/${RUNNAME}
    ensure_directory "${DEST}"
    cp ${BASEDIR}/source/shuttermap.fits "${DEST}/${SHUTTERMAP}"
}


create_master_flat() {
    #Create MasterFlat
    echo "Create MasterFlat"
    CMD="python ${SCRIPTDIR}/pipeflat.py $FLATLIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits $SHUTTERMAP ${RUNNAME}_MasterFlat.fits ${WORKINGDIR}/Reduction/output/${RUNNAME}"
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
        CMD="python ${SCRIPTDIR}/pipered.py ${WORKINGDIR}/OriginalData/output/$IMAGELIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits $SHUTTERMAP ${RUNNAME}_MasterFlat.fits ${WORKINGDIR}/Reduction/output/${RUNNAME} ${WORKINGDIR}/Reduction/output/${RUNNAME}/${IMAGELIST%.*}"
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
    reduce_images "${IMAGELISTS}"
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

    for FILELIST in ${WORKINGDIR}/OriginalData/output/${RUNNAME}_image_*.list; do
        local readonly basename=${FILELIST#${WORKINGDIR}/OriginalData/output/}
        local readonly jobname=${basename%.*}
        local readonly output_directory=${WORKINGDIR}/AperturePhot/output/${RUNNAME}/${jobname}
        local readonly image_filelist=${output_directory}/filelist.txt

        ensure_directory "$output_directory"
        find ${WORKINGDIR}/Reduction/output/${RUNNAME}/${jobname} -name 'proc*.fits' > ${image_filelist}
        python ${SCRIPTDIR}/NGTS_workpackage/bin/ZLP_app_photom.py \
            --confmap ${CONFMAP} \
            --catfile ${GIVEN_INPUTCATALOGUE} \
            --nproc ${CORES} \
            --filelist ${image_filelist} \
            --outdir ${output_directory} \
            --dist ${BASEDIR}/source/initial_wcs_solution.pickle \
            --catpath ${BASEDIR}/source/catcache

        # Condense the photometry
        python ${SCRIPTDIR}/NGTS_workpackage/bin/ZLP_create_outfile.py \
            --outdir ${output_directory} \
            --nproc ${CORES} \
            ${image_filelist}

    done
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
    set +o nounset
    export PYTHONPATH=${BASEDIR}/scripts/NGTS_workpackage:${BASEDIR}/scripts:$PYTHONPATH
    echo "Environment set up"
    set -o nounset
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

main 2>&1 | tee ${RUNNAME}.log
