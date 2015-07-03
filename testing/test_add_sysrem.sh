#!/usr/bin/env sh

set -eu

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

    run_test test_output.fits test_tamout.fits

}

main
