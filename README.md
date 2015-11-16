# zlp-script

This script runs the ZLP in its entirety

* Original author: Philipp
* Maintainer: Simon

**:warning: Please if you make any changes, perform these in a new branch (*not master!*) and either inform me or submit a pull request. Master is for tested ready code. :warning:**

## Branches

* `no-flat`: run the pipeline without a flat field correction
* `narrower-sky`: shrink the sky background size parameter from 64 to 32

## Documentation

Documentation can be found in the `doc` subdirectory, and compiled (if required) into html by running the Makefile in the doc directory:

`make -C doc`
# zlp-subtraction
