#!/usr/bin/env bash

set -o nounset
set -o errexit
set -o pipefail

abspath() {
    python -c "import os; print os.path.realpath('${1}')"
}


if [[ $# -ne 7 ]] && [[ $# -ne 8 ]]; then
    cat >&2 <<-EOF
  Usage: $0 <runname> <root-directory> <input-catalogue> <initial-wcs-solution> <confidence-map> <shuttermap> <wcsfit-reference-frame> [master-flat]

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
                      IMAGE*.fits.bz2

  * input-catalogue

  The list of coordinates to place apertures at

  * initial_wcs_solution

  The initial wcs solution computed by Tom's MCMC code to compute distortion
  parameters

  * confidence-map
  * shuttermap
  * wcsfit-reference-frame
  * master-flat

  Custom master flat to use, overriding the flat computed from the supplied data
EOF
    exit 1
fi

# command line arguments
readonly BASEDIR=$(abspath $(dirname $0))
readonly RUNNAME=${1}
readonly WORKINGDIR=$(abspath ${2})
readonly GIVEN_INPUTCATALOGUE=$3
readonly WCSSOLUTION=$4
readonly CONFMAP=$5
readonly SHUTTERMAP=$6
readonly WCSFIT_REFERENCE_FRAME=$7

readonly IMGDIRS=${WORKINGDIR}/OriginalData/images/**/*
readonly SCRIPTDIR=${BASEDIR}/scripts

readonly BIASLIST=${WORKINGDIR}/OriginalData/output/${RUNNAME}_bias.list
readonly DARKLIST=${WORKINGDIR}/OriginalData/output/${RUNNAME}_dark.list
readonly FLATLIST=${WORKINGDIR}/OriginalData/output/${RUNNAME}_flat.list
readonly CORES=$(python -c "import multiprocessing; print multiprocessing.cpu_count()")
readonly APSIZE=3

echo "Using ${CORES} cores"

# Which tasks to run. Set to "1" if the task should be run otherwise "0".
readonly T1="1" # create input lists, default: 1
readonly T2="1" # create masterbias, default: 1
readonly T3="1" # create masterdark, default: 1
readonly T4="1" # copy temporary shutter map, default: 1
readonly T5="1" # create masterflat, default: 1
readonly T6="1" # reduce science images, default: 1
readonly T7="1" # perform photometry, default: 1
readonly T8="0" # run image subtraction, default: 0
readonly T9="1" # detrend, default: 1
readonly T10="1" # detrend with lightcurves, default: 1
readonly T11="1" # Make qa plots, default: 1


# Zero Level Pipeline
# Here all the commands are listed.
# this script can be run  from command line. to do the whole pipeline.


create_input_lists() {
    echo "Create lists with Images"
    CMD="python ${SCRIPTDIR}/createlists.py \"$IMGDIRS\" IMAGE bz2 $RUNNAME"
    echo $CMD
    ${CMD}
}

create_master_bias() {
    # Create MasterBias
    echo "Create MasterBias"
    CMD="python ${SCRIPTDIR}/zlp-reduction/bin/pipebias.py $BIASLIST ${RUNNAME}_MasterBias.fits ${WORKINGDIR}/Reduction/output/${RUNNAME}"
    echo ${CMD}
    ${CMD}
}

create_master_dark() {
    #Create MasterDark
    echo "Create MasterDark"
    CMD="python ${SCRIPTDIR}/zlp-reduction/bin/pipedark.py $DARKLIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits ${WORKINGDIR}/Reduction/output/${RUNNAME}"
    echo ${CMD}
    ${CMD}
}

copy_temporary_shuttermap() {
    echo "Copying temporary shutter map"
    # # !!!! be carefull, shuttermap not yet automatically created. will be copied manualy
    # #
    DEST=${WORKINGDIR}/Reduction/output/${RUNNAME}
    ensure_directory "${DEST}"
    cp ${SHUTTERMAP} "${DEST}/$(basename ${SHUTTERMAP})"
}


create_master_flat() {
    #Create MasterFlat
    echo "Create MasterFlat"
    CMD="python ${SCRIPTDIR}/zlp-reduction/bin/pipeflat.py $FLATLIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits $SHUTTERMAP ${RUNNAME}_MasterFlat.fits ${WORKINGDIR}/Reduction/output/${RUNNAME}"
    echo ${CMD}
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
        IMAGELIST=${IMAGELIST#${WORKINGDIR}/OriginalData/output/}
        ensure_directory ${WORKINGDIR}/Reduction/output/${RUNNAME}/${IMAGELIST%.*}
        CMD="python ${SCRIPTDIR}/zlp-reduction/bin/pipered.py ${WORKINGDIR}/OriginalData/output/$IMAGELIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits $SHUTTERMAP ${RUNNAME}_MasterFlat.fits ${WORKINGDIR}/Reduction/output/${RUNNAME} ${WORKINGDIR}/Reduction/output/${RUNNAME}/${IMAGELIST%.*}"
        echo ${CMD}
        ${CMD}
    done
}

any_filelists() {
    local readonly IMAGELISTS=$1
    ls ${IMAGELISTS} 2>/dev/null >/dev/null
}

reduce_science_images() {
    echo "Reduce Science Images"
    IMAGELISTS=$WORKINGDIR/OriginalData/output/${RUNNAME}_image_*.list
    if $(any_filelists ${IMAGELISTS}); then
        reduce_images "${IMAGELISTS}"
    fi
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

iterate_and_act_on_lists() {
    local readonly lists="$1"
    local readonly action="$2"

    if $(any_filelists ${lists}); then
        for fname in ${lists}; do
            eval "${action} ${fname}"
        done
    fi
}

shrink_catalogue_directory() {
    local readonly catcachedir=$1
    ls ${catcachedir} | grep cch_ | while read fname; do
        local readonly filepath=${catcachedir}/${fname}
        python ${BASEDIR}/scripts/shrink_wcs_reference.py ${filepath} -o ${filepath}
    done
}

single_perform_aperture_photometry() {
    local filelist=$1
    local readonly basename=${filelist#${WORKINGDIR}/OriginalData/output/}
    local readonly jobname=${basename%.*}
    local readonly output_directory=${WORKINGDIR}/AperturePhot/output/${RUNNAME}/${jobname}
    local readonly image_filelist=${output_directory}/filelist.txt

    ensure_directory "$output_directory"
    find ${WORKINGDIR}/Reduction/output/${RUNNAME}/${jobname} -name 'proc*.fits' > ${image_filelist}
    python ${SCRIPTDIR}/zlp-photometry/bin/ZLP_app_photom.py \
        --confmap ${CONFMAP} \
        --catfile ${GIVEN_INPUTCATALOGUE} \
        --nproc ${CORES} \
        --filelist ${image_filelist} \
        --outdir ${output_directory} \
        --dist ${WCSSOLUTION} \
        --apsize ${APSIZE} \
        --wcsref ${WCSFIT_REFERENCE_FRAME}

    PIPELINESHA=$(extract_pipeline_sha $(dirname $0))

    # Condense the photometry
    python ${SCRIPTDIR}/zlp-condense/zlp_condense.py \
        --output "${output_directory}/output.fits" \
        --sha "${PIPELINESHA}" \
        $(cat ${image_filelist} | sed 's/.fits/.fits.phot/')
}

perform_aperture_photometry() {
    echo "Running aperture photometry"
    cd ${WORKINGDIR}/AperturePhot

    local readonly filelists=${WORKINGDIR}/OriginalData/output/${RUNNAME}_image_*.list
    iterate_and_act_on_lists ${filelists} single_perform_aperture_photometry
}

run_detrending() {
    SYSREM=sysrem
    if hash ${SYSREM} 2>/dev/null; then
        echo "Detrending with SYSREM"

        local readonly photomfile=$(find ${WORKINGDIR}/AperturePhot/output -name 'output.fits')
        if [ ! -z "${photomfile}" ]; then
            local readonly output_directory=$(dirname $photomfile)
            local readonly outfile=${output_directory}/tamout.fits
            echo "Running sysrem to create ${outfile}"

            if [ -z ${NOSYSREM:-} ]; then
                ${SYSREM} ${photomfile} ${outfile}
                python ${BASEDIR}/scripts/combine_with_sysrem.py -v -p ${photomfile} -t ${outfile}
            else
                echo '*** sysrem has been disabled with envar: NOSYSREM. unset to run sysrem'
            fi
        else
            echo "Cannot find photometry output files" >&2
        fi
    else
        echo "Cannot find sysrem binary ${SYSREM}" >&2
    fi
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
    if [ -z ${DISABLE_ANACONDA:-} ]; then
        # Allow the user to override the anaconda path variable
        if [ -z ${ANACONDA_PATH:-} ]; then
        # If anaconda is available, use it
        case `hostname` in
            ngtshead*)
            ANACONDA_PATH=/home/sw/anaconda
            ;;
            *)
            ANACONDA_PATH=${HOME}/anaconda
            ;;
        esac
        fi

        PARANAL_ANACONDA_PATH=/usr/local/anaconda

        if [[ -d ${ANACONDA_PATH} ]]; then
            export PATH=${PARANAL_ANACONDA_PATH}/bin:${ANACONDA_PATH}/bin:${PATH}
        fi
    fi

    echo "Using python: $(which python)"

    set +o nounset
    export PATH=/usr/local/pipeline/bin:${PATH}
    export PYTHONPATH=${BASEDIR}/scripts/zlp-photometry:${BASEDIR}/scripts:${BASEDIR}/scripts/zlp-input-catalogue:$PYTHONPATH
    case "$(hostname -s)" in
        ngts*)
            export IERS_DATA=/usr/local/pipeline/data
            export JPLEPH_DATA=${IERS_DATA}/linux_p1550p2650.430t
            ;;
        mbp*)
            export IERS_DATA=${HOME}/.local/data
            export JPLEPH_DATA=${IERS_DATA}/linux_p1550p2650.430t
            ;;
    esac

    if [ ! -z ${IERS_DATA} ]; then
        echo "IERS data path: ${IERS_DATA}"
    fi

    if [ ! -z ${JPLEPH_DATA} ]; then
        echo "JPLEPH data path: ${JPLEPH_DATA}"
    fi

    # LD_LIBRARY_PATH for sysrem
    LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-}:/opt/intel/composer_xe_2013_sp1.0.080/compiler/lib/intel64

    echo "Environment set up"
    set -o nounset
}

setup_directory_structure() {
    for subdir in OriginalData/output AperturePhot Reduction Reduction/output; do
        local dirpath=${WORKINGDIR}/${subdir}
        ensure_directory ${WORKINGDIR}/${subdir}
    done
}

run_lightcurves_detrending() {
    if hash lightcurves-casu 2>/dev/null; then
        local readonly ref=$GIVEN_INPUTCATALOGUE
        local readonly photomfile=$(find ${WORKINGDIR}/AperturePhot/output -name 'output.fits' -print)
        if [ ! -z "${photomfile}" ]; then
            local readonly output_directory=$(dirname $photomfile)
            local readonly outfile=${output_directory}/casu-lightcurves-out.fits
            local readonly number_of_coefficients=2
            local readonly source_files_dir=${WORKINGDIR}/Reduction/output/${RUNNAME}
            echo "Running casu lightcurves file to create ${outfile}"

            lightcurves-casu -f ${number_of_coefficients} -o ${outfile} -p ${ref} $(find ${source_files_dir} -name 'proc*.phot')
            python ${BASEDIR}/scripts/combine_with_casu_detrended.py -v -p ${photomfile} -d ${outfile}
        fi
    else
        echo "Cannot find CASU lightcurves binary" >&2
    fi
}

generate_qa_plots() {
    bash ${BASEDIR}/scripts/zlp-qa/run.sh \
        ${WORKINGDIR} \
        ${WORKINGDIR}/QualityAssessment
}

extract_pipeline_sha() {
    local readonly dirname="$1"
    (cd $dirname && git rev-parse HEAD)
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

    [ "$T6" = "1" ] && reduce_science_images

    cd ${WORKINGDIR}
    [ "$T7" = "1" ] && perform_aperture_photometry
    
    # [ "$T8" = "1" ] && perform_image_subtraction

    [ "$T9" = "1" ] && run_detrending

    [ "$T10" = "1" ] && run_lightcurves_detrending

    [ "$T11" = "1" ] && generate_qa_plots
}

main 2>&1 | tee ${RUNNAME}.log
