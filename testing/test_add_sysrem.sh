#!/usr/bin/env sh

set -eu

find_file() {
    find testdata/AperturePhot -name $1
}

does_file_exist() {
    FNAME=$(find_file $1)
    if [ -z ${FNAME} ]; then
        return 1
    else
        return 0
    fi
}


main() {
    if does_file_exist "output.fits"; then
        if does_file_exist "tamout.fits"; then
            exit 0
        fi
    fi

    echo "Cannot find either output.fits or tamout.fits. Please run the pipeline test" >&2
    exit 1
}

main
