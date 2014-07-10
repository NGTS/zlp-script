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

To run the code, the main `ZLP_pipeline.sh` script is used. It requires the following arguments (in order):

* job name
* root directory
* input catalogue
* initial wcs solution
* confidence map
* shuttermap
* wcsfit reference frame

To get a reminder, run `ZLP_pipeline.sh -h` and the usage will be printed out. See the section in input arguments for details of what these mean.

This script calls into scripts in the `scripts` subdirectory for tasks.

Inside the run script are flags which can be changed if e.g. only reduction is wanted. These flags look like:

```
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
```

The above are the defaults and will produce a single lightcurve file out of a directory of raw images and calibration frames. The reduction tasks cannot be disabled as the pipeline will break.

### Required initial data structure

The data structure must be set up manually before a run. 

#### Root directory

Whatever is used for the `<root-directory>` argument must look like:

```
<root-directory>
`-- OriginalData
    `-- images
      `-- <one directory per date>
        `-- <action_* subdirectory>
          `-- IMAGE*.fits
```

so for example the test dataset used looks initially like:

```
testdata
`-- OriginalData
    `-- images
        `-- 20140626
            |-- action2663_biasFrames
            |   |-- IMAGE80420140625193940.fits         |
            |   |-- IMAGE80420140625193943.fits         |
            |   |-- IMAGE80420140625193946.fits         | - bias frames
            |   |-- IMAGE80420140625193948.fits         |
            |   |-- IMAGE80420140625193950.fits         |
            |   `-- IMAGE80420140625193952.fits         |
            |-- action2667_darkFrames
            |   |-- IMAGE80420140625194446.fits         |
            |   |-- IMAGE80420140625194548.fits         |
            |   |-- IMAGE80420140625194650.fits         | - dark frames
            |   |-- IMAGE80420140625194752.fits         |
            |   |-- IMAGE80420140625194855.fits         |
            |   `-- IMAGE80420140625194957.fits         |
            |-- action2675_flatField
            |   |-- IMAGE80420140625201705.fits         |
            |   |-- IMAGE80420140625201712.fits         |
            |   |-- IMAGE80420140625201718.fits         |
            |   |-- IMAGE80420140625201725.fits         |
            |   |-- IMAGE80420140625201731.fits         |
            |   |-- IMAGE80420140625201737.fits         | - flat frames
            |   |-- IMAGE80420140625201744.fits         |
            |   |-- IMAGE80420140625201751.fits         |
            |   |-- IMAGE80420140625201757.fits         |
            |   |-- IMAGE80420140625201803.fits         |
            |   `-- IMAGE80420140625201810.fits         |
            `-- action2684_exposureCycle
                |-- IMAGE80420140625211323.fits         |
                |-- IMAGE80420140625211329.fits         |
                |-- IMAGE80420140625211337.fits         | - science images
                |-- IMAGE80420140625211342.fits         |
                `-- IMAGE80420140625211354.fits         |
```

running with `ZLP_pipeline.sh <runname> testdata ...`

At least one file, probably two must be present in each subdirectory for the pipeline to work. *If no data of a particular type e.g. bias, dark etc. was taken then copy some previous data in.*


#### Extra files


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

### Required input files
### Creating the input files (if required)
## Testing
