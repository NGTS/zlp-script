#!/usr/bin/env sh

set -eu

BASEDIR=$(dirname $0)/..

find_file() {
    find testing/data -name $1
}

does_file_exist() {
    FNAME=$(find_file $1)
    if [ -z ${FNAME} ]; then
        return 1
    else
        return 0
    fi
}


run_test() {
    readonly outputname=$1
    readonly tamname=$2

    readonly test_fname="$TMPDIR/test_photom.fits"
    cp $outputname $test_fname

    python $BASEDIR/scripts/combine_with_sysrem.py -p $test_fname -t $tamname -v

    verify
}

verify() {
    python <<EOF
from astropy.io import fits

with fits.open("$test_fname") as infile:
    assert "tamflux" in infile

    imagelist = infile['imagelist'].data
    catalogue = infile['catalogue'].data

imagelist_names = set([col.name for col in imagelist.columns])
catalogue_names = set([col.name for col in catalogue.columns])

# assert 'AJ' in imagelist_names, "Cannot find AJ imagelist column"
# assert 'TAM_ZP' in imagelist_names, "Cannot find tamuz zero point imagelist column"
assert 'CI' in catalogue_names, 'Cannot find CI catalogue column'
EOF
}


main() {
    if ! does_file_exist "test_output.fits"; then
        echo "Cannot find photometry file" >&2
        exit 1
    fi

    if ! does_file_exist "test_tamout.fits"; then
        echo "Cannot find tamuz file" >&2
        exit 1
    fi

    run_test $(find_file test_output.fits) $(find_file test_tamout.fits)

}

main
