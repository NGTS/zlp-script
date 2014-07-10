# Zero Level Pipeline

## Installation

To install the pipeline, the zipped source code can be uncompressed into a directory. The code is self-contained so only looks within itself (like a self imposed `chroot`).

All scripts used are in the `scripts` subdirectory and consist of python files or shell scripts.

The code has dependencies on external tools:

### Dependencies

* python
* cfitsio
* casutools (customised to our needs)

Python packages:

* numpy
* scipy
* emcee (optional, only used for initial wcs solver)
* matplotlib
* fitsio
* astropy

## Running

To run the code, the main `ZLP_pipeline.sh` script is used. S

```
  Usage: $0 <runname> <root-directory> <input-catalogue> <initial-wcs-solution> <confidence-map> <shuttermap> <wcsfit-reference-frame>

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

  * confidence-map
  * shuttermap
  * wcsfit-reference-frame
```

### Required initial data structure

### Required input files
### Creating the input files (if required)
## Testing
