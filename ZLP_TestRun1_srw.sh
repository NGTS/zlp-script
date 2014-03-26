#!/bin/bash

set -e

IMGDIRS=/ngts/pipedev/OriginalData/images/201307[0-1][1,4,5]/*
RUNNAME="SimonTest1"

WORKINGDIR=/ngts/pipedev
BIASLIST=${WORKINGDIR}/OriginalData/output/${RUNNAME}_bias.list
DARKLIST=${WORKINGDIR}/OriginalData/output/${RUNNAME}_dark.list
FLATLIST=${WORKINGDIR}/OriginalData/output/${RUNNAME}_flat.list
SHUTTERMAP=${WORKINGDIR}/Reduction/${RUNNAME}/shuttermap.fits
CORES=8


T1="0" # create input lists
T2="0" # create masterbias
T3="0" # create masterdark
T4="1" # copy temporary shutter map
T5="0" # create masterflat
T6="0" # reduce dithered images
T7="0" # reduce science images
T8="0" # wait for jobs to finish
T9="0" # create input catalogues

T12="0" # run image subtraction


# Zero Level Pipeline
# Here all the commands are listed.
# this script can be run  from command line. to do the whole pipeline.


create_input_lists() {
    echo "Create lists with Images"
    /ngts/pipedev/OriginalData/scripts/createlists.py "$IMGDIRS" IMAGE fits $RUNNAME 
}

create_master_bias() {
    # Create MasterBias
    echo "Create MasterBias"
    echo "python /home/ag367/progs/pipebias.py $BIASLIST ${RUNNAME}_MasterBias.fits ${WORKINGDIR}/Reduction/${RUNNAME}"
    echo "python /home/ag367/progs/pipebias.py $BIASLIST ${RUNNAME}_MasterBias.fits ${WORKINGDIR}/Reduction/${RUNNAME}" | qsub -N ${RUNNAME}_BIAS -sync y
}

create_master_dark() {
    #Create MasterDark
    echo "Create MasterDark"
    echo "python /home/ag367/progs/pipedark.py $DARKLIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits ${WORKINGDIR}/Reduction/${RUNNAME}"
    echo "python /home/ag367/progs/pipedark.py $DARKLIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits ${WORKINGDIR}/Reduction/${RUNNAME}" | qsub -N ${RUNNAME}_DARK -sync y
}

copy_temporary_shuttermap() {
    echo "Copying temporary shutter map"
    # # !!!! be carefull, shuttermap not yet automatically created. will be copied manualy
    # #
    DEST=`dirname ${SHUTTERMAP}`
    test -d ${DEST} || mkdir -p ${DEST}
    cp /home/ag367/test/shuttermap.fits ${SHUTTERMAP}
    # #
    # # needs to be updated
}


create_master_flat() {
    #Create MasterFlat
    echo "Create MasterFlat"
    echo "python /home/ag367/progs/pipeflat.py $FLATLIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits $SHUTTERMAP ${RUNNAME}_MasterFlat.fits ${WORKINGDIR}/Reduction/${RUNNAME}"
    echo "python /home/ag367/progs/pipeflat.py $FLATLIST ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits $SHUTTERMAP ${RUNNAME}_MasterFlat.fits ${WORKINGDIR}/Reduction/${RUNNAME}" | qsub -N ${RUNNAME}_FLAT -sync y
}

reduce_dithered_images() {
    #Reduce Dithered Images
    echo "Reduce Dithered Images"
    DITHJOBS=""
    counter="0"
    for DITHERFILE in ${WORKINGDIR}/OriginalData/output/${RUNNAME}_dither_*.list
    do 
        DITHERFILE=${DITHERFILE#${WORKINGDIR}} 
        DITHERFILE=${DITHERFILE#/OriginalData/output/} 
        mkdir /ngts/pipedev/Reduction/${RUNNAME}/${DITHERFILE%.*}
        echo "python /home/ag367/progs/pipered.py ${WORKINGDIR}/OriginalData/output/$DITHERFILE ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits $SHUTTERMAP ${RUNNAME}_MasterFlat.fits ${WORKINGDIR}/Reduction/${RUNNAME} ${WORKINGDIR}/Reduction/${RUNNAME}/${DITHERFILE%.*}"
        echo "python /home/ag367/progs/pipered.py ${WORKINGDIR}/OriginalData/output/$DITHERFILE ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits $SHUTTERMAP ${RUNNAME}_MasterFlat.fits ${WORKINGDIR}/Reduction/${RUNNAME} ${WORKINGDIR}/Reduction/${RUNNAME}/${DITHERFILE%.*}" | qsub -N ${DITHERFILE%.*}
        if [ "$counter" -ne "0" ] ; then DITHJOBS=${DITHJOBS}"," ; fi 
        DITHJOBS=${DITHJOBS}${DITHERFILE%.*}
        echo $DITHJOBS
        counter="1"
    done
}

reduce_science_images() {
    # Reduce Science Images
    echo "Reduce Science Images"
    IMGJOBS=""
    for IMAGEFILE in $WORKINGDIR/OriginalData/output/${RUNNAME}_image_*.list
    do 
        IMAGEFILE=${IMAGEFILE#${WORKINGDIR}} 
        IMAGEFILE=${IMAGEFILE#/OriginalData/output/} 
        mkdir /ngts/pipedev/Reduction/${RUNNAME}/${IMAGEFILE%.*}
        echo "python /home/ag367/progs/pipered.py ${WORKINGDIR}/OriginalData/output/$IMAGEFILE ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits $SHUTTERMAP ${RUNNAME}_MasterFlat.fits ${WORKINGDIR}/Reduction/${RUNNAME} ${WORKINGDIR}/Reduction/${RUNNAME}/${IMAGEFILE%.*}"
        echo "python /home/ag367/progs/pipered.py ${WORKINGDIR}/OriginalData/output/$IMAGEFILE ${RUNNAME}_MasterBias.fits ${RUNNAME}_MasterDark.fits $SHUTTERMAP ${RUNNAME}_MasterFlat.fits ${WORKINGDIR}/Reduction/${RUNNAME} ${WORKINGDIR}/Reduction/${RUNNAME}/${IMAGEFILE%.*}" | qsub -N ${IMAGEFILE%.*}
        if [ "$counter" -ne "0" ] ; then IMGJOBS=${IMGJOBS}"," ; fi 
        IMGJOBS=${IMGJOBS}${IMAGEFILE%.*}
        echo $IMGJOBS
        counter="1"
    done
}

wait_for_jobs() {
    # Wait until reduction is finished
    echo "Wait until reduction is finished"
    echo "qsub -hold_jid ${DITHJOBS}${IMGJOBS} -cwd ${WORKINGDIR}/wait.sh"
    qsub -hold_jid ${DITHJOBS}${IMGJOBS} -N WAIT  -sync y -cwd ${WORKINGDIR}/wait.sh 
}


create_input_catalogue() {
    # Frame Selection / Quality and Integrity Check

    # Create Input Catalogue if not already exists for imagelists
    cd /ngts/pipedev/InputCatalogue
    for DITHERFILE in ${WORKINGDIR}/OriginalData/output/${RUNNAME}_dither_*.list
    do 
        DITHERFILE=${DITHERFILE#${WORKINGDIR}}
        DITHERFILE=${DITHERFILE#/OriginalData/output/}
        DITHERFILE=${DITHERFILE%.*}
        echo $DITHERFILE
        mkdir /ngts/pipedev/InputCatalogue/output/${RUNNAME}
        mkdir /ngts/pipedev/InputCatalogue/output/${RUNNAME}/${DITHERFILE}
        find /ngts/pipedev/Reduction/${RUNNAME}/${DITHERFILE} -name '*.fits' > /ngts/pipedev/InputCatalogue/${DITHERFILE}.txt
        echo "/ngts/pipedev/InputCatalogue/run_on_directory.sh ./${DITHERFILE}.txt ./srw_confidence.fits ./output/${RUNNAME}"
        /ngts/pipedev/InputCatalogue/run_on_directory.sh ./${DITHERFILE}.txt ./srw_confidence.fits ./output/${RUNNAME}/${DITHERFILE}
        # qsub /ngts/pipedev/InputCatalogue/run_on_directory.sh ./${DITHERFILE}.txt ./srw_confidence.fits ./output/${RUNNAME}/${DITHERFILE}
    done
    cd /ngts/pipedev
}

# Do Aperture Photometry for Image list


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




# Do photometry on subtracted Images

main() {
    cd ${WORKINGDIR}/OriginalData 
    [ "$T1" = "1" ] && create_input_lists

    # ( cd ${WORKINGDIR}/Reduction
    # [ "$T2" = "1" ] && create_master_bias 

    # [ "$T3" = "1" ] && create_master_dark 

    [ "$T4" = "1" ] && copy_temporary_shuttermap

    # [ "$T5" = "1" ] && create_master_flat 

    # [ "$T6" = "1" ]&&  reduce_dithered_images 

    # [ "$T7" = "1" ] && reduce_science_images 

    # [ "$T8" = "1" ] && wait_for_jobs )

    # [ "$T9" = "1" ] && create_input_catalogue 
}

main
