<!-- -*- coding: utf-8 -*- -->
Zero Level Pipeline
===================

* [Quickstart](#user-content-quickstart)
* [Running](#user-content-running)
  * [Required initial data structure](#user-content-required-initial-data-structure)
    * [Root directory](#user-content-root-directory)
    * [Required input files](#user-content-required-input-files)
  * [Creating input files](#user-content-creating-input-files)
* [Possible errors](#user-content-possible-errors)
* [Installation](#user-content-installation)
  * [Dependencies](#user-content-dependencies)
* [Testing](#user-content-testing)

<a name='quickstart'></a>Quickstart
----------

1. Initialise the output directory to the correct structure
2. Think of a job name
3. Run `ZLP_pipeline.sh` with the output directory and extra reference files
4. Get some coffee...

<a name='running'></a>Running
-------

To run the code, the main `ZLP_pipeline.sh` script is used. It requires the following arguments (in order):

* job name
* root directory
* input catalogue
* initial wcs solution
* confidence map
* shuttermap
* wcsfit reference frame

Any paths must be absolute, so start with '/' e.g. '/home/ngts/...'. To get a reminder of any arguments or their order, run `ZLP_pipeline.sh -h` and the usage will be printed out. See the section in input arguments for details of what these mean.

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

### <a name='required-initial-data-structure'></a>Required initial data structure

The data structure must be set up manually before a run. 

#### <a name='root-directory'></a>Root directory

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

running with `ZLP_pipeline.sh <runname> testdata ...`. The images and/or directories can be soft links to prevent duplicating data. No raw data is overwritten so no data will be lost.

At least one file, probably two must be present in each subdirectory for the pipeline to work. *If no data of a particular type e.g. bias, dark etc. was taken then copy some previous data in.* All of the input images should have the same size i.e. 2088x2048 pixels with 20 extra pixels on the left and right for pre/overscan. These are the same format as raw images from the instrument.


#### <a name='required-input-files'></a>Required input files

Some extra files are required for the pipeline to function. These are (in order of arguments to `ZLP_pipeline.sh:

    * input-catalogue

The positions in ra/dec where apertures are to be placed. This file is a fits file where hdu 1 (0-indexed) is a binary table consisting of `RA` and `DEC` columns in *radians*. This can be constructed simply by running `imcore` on a single image, or ideally from running `imcore` on a group of stacked images. Whatever the source image, the output format is compatible.

    * initial-wcs-solution

The initial wcs solution is stamped into the fits images before the refinement step to both conform the keywords standard into one understood by casutools, and to ensure the true solution is not far away from the assumed initial solution. This is computed through MCMC analysis to determine the distortion parameters and a scaling from stamped keywords `TEL_RA` and `TEL_DEC` to true central coordinates. The astrometry step then takes over and refines the solution.

The file passed is a pickled python dictionary. A tool to construct this file from the final MCMC result is given as TBD.

    * confidence-map

This is not currently computed by the pipeline, but can be constructed by scaling a master flat frame such that the median of the resulting frame is 100.

    * shuttermap

This is not currently computed by the pipeline. The code to generate one has not been written yet (as of Thu Jul 10 2014), but a sample one is supplied. Alternatively a frame of the correct size (2048x2088) of zeros can be supplied if no shuttermap is available.

    * wcsfit-reference-frame

The wcsfit reference frame must contain external catalogue information, and is a fits file where hdu 1 (0-indexed) is a binary table containing `RA`, `DEC` and `Jmag` therefore a 2MASS catalogue is prefered. It is used during the astrometric solution step to determine where each of our detected objects *should* be on the sky.

### <a name='creating-input-files'></a>Creating the input files (if required)

    * input-catalogue

This can be constructed by running `imcore` on a frame. Ideally a stacked image or low sky background and high airmass frame, but any frame will do.

    * initial-wcs-solution

This must be constructed from a python dictionary to the pickle file format using TBD.

    * confidence-map

This can be an image of value 100

    * shuttermap

This can be an image of value 0

    * wcsfit-reference-frame

This must be a fits file where hdu 1 is a table with RA and DEC columns of units degrees, and a Jmag column.

With an internet connection, this can be created by using wcsfit to solve a single image, and running `scripts/shrink_wcs_reference.py` on the file `catcache/cch_00000001` i.e.:

`python scripts/shrink_wcs_reference.py catcache/cch_00000001 -o wcsfit-reference.fits`.

This also has the bonus of only including stars within the J magnitude range 8 - 14 speeding up solving time.

<a name='possible-errors'></a>Possible errors
---------------

The script may output lots of `RuntimeError`s which is normal. Not ideal but not harmful to the analysis, it most likely means some non-detections or apertures outside the chip are causing divide by zero errors, or nan arithmetic.

Some possibly likely errors are:

* error with `cir_getstds`

This call is from `wcsfit` and means that no standard reference stars were found to match the frame to. This may mean that the script is trying to connect to the internet and failing, or that the reference catalogue does not match the frame.

<a name='installation'></a>Installation
------------

To install the pipeline, the zipped source code can be uncompressed into a directory. The code is self-contained so only looks within itself (like a self imposed `chroot`).

All scripts used are in the `scripts` subdirectory and consist of python files or shell scripts.

The code has dependencies on external tools:

### <a name='dependencies'></a>Dependencies

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

<a name='testing'></a>Testing
-------

The example test data should be unpacked into a directory at the same level as the `ZLP_pipeline.sh` script.  An example directory structure is shown below.

```
|-- images
|   `-- 20140626
|       |-- action2663_biasFrames
|       |   |-- IMAGE80420140625193940.fits
|       |   |-- IMAGE80420140625193943.fits
|       |   |-- IMAGE80420140625193946.fits
|       |   |-- IMAGE80420140625193948.fits
|       |   |-- IMAGE80420140625193950.fits
|       |   `-- IMAGE80420140625193952.fits
|       |-- action2667_darkFrames
|       |   |-- IMAGE80420140625194446.fits
|       |   |-- IMAGE80420140625194548.fits
|       |   |-- IMAGE80420140625194650.fits
|       |   |-- IMAGE80420140625194752.fits
|       |   |-- IMAGE80420140625194855.fits
|       |   `-- IMAGE80420140625194957.fits
|       |-- action2675_flatField
|       |   |-- IMAGE80420140625201705.fits
|       |   |-- IMAGE80420140625201712.fits
|       |   |-- IMAGE80420140625201718.fits
|       |   |-- IMAGE80420140625201725.fits
|       |   |-- IMAGE80420140625201731.fits
|       |   |-- IMAGE80420140625201737.fits
|       |   |-- IMAGE80420140625201744.fits
|       |   |-- IMAGE80420140625201751.fits
|       |   |-- IMAGE80420140625201757.fits
|       |   |-- IMAGE80420140625201803.fits
|       |   `-- IMAGE80420140625201810.fits
|       `-- action2684_exposureCycle
|           |-- IMAGE80420140625211323.fits
|           |-- IMAGE80420140625211329.fits
|           |-- IMAGE80420140625211337.fits
|           |-- IMAGE80420140625211342.fits
|           `-- IMAGE80420140625211354.fits
|-- initial_wcs_solution.pickle
|-- input-catalogue.fits
|-- shuttermap.fits
|-- srw_confidence.fits
`-- wcs-reference-frame.fits
```

Running the script `test.sh <directory of unpacked test data>` should initialise the output directory and run the pipeline passing in any arguments needed such as the extra files required. By using this test script the success or failure of the pipeline can be determined with a small data set.
