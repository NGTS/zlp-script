CASUTools primer
----------------

The CASUTools suite consists of astronomy tools of which we use four:

* imstack
* imcore
* imcore_list
* wcsfit

All of the tools include a small help reminder with the `-h` flag, and these are included below with the relevant tools.

### `imcore`

`imcore` is a tool similar to sextractor, used for extracting sources from on sky images. The required arguments are:

  * image file - the source image
  * confidence map, can be the string "noconf" to ignore confidence map usage
  * outfile - the output catalogue containing information about the extracted sources
  * ipix - number of pixels above detection threshold to include
  * thresh - threshold in sigmas above the sky background for included stars

Important optional parameters are:

  * rcore - aperture size in pixels, typically set to 2 or 3
  * filtfwhm - used for source separation, typically set to 2 or 3
  * ell - create region files which can be loaded into ds9 to see which sources were extracted

```
Usage: imcore infile confmap outfile ipix thresh
[--(no)crowd (yes)] [--rcore=5] [--nbsize=64] [--filtfwhm=3]
[--(no)ell (yes)] [--(no)verbose (no)] [--cattype=6]
```

**Example usage**

`imcore file.fits noconf catalogue.fits 2 7 --rcore 3 --filtfwhm 3 --noell`

---

### `imcore_list`

`imcore_list` is a simple list driven photometry tool which places apertures down at the specified coordinates. These coordinates come from the `input-catalogue` file which is a fits file where hdu 1 is a binary table with RA and DEC in radians.

The `infile`, `confmap`, `outfile` and `thresh` arguments remain the same as above, but with the `listfile` argument added to pass in the input catalogue.

```
Usage: imcore_list infile confmap listfile outfile thresh
[--rcore=5] [--nbsize=64] [--trans=] [--(no)ell (yes)]
[--(no)verbose (no)] [--cattype=1]
```

**Example usage**

`imcore_list file.fits noconf input-catalogue.fits catalogue.fits 7`

---

### `wcsfit`

`wcsfit` computes an astrometric solution for a single image, and stamps into the files header.

The program requires the input image and the catalogue of source positions as extracted by `imcore`.

The primary mode queries a remote catalogue server which therefore requires the internet, which we may not have. It does support a `localfits` argument to use a local fits file.

```
Usage: wcsfit infile incat
[--catsrc=viz2mass] [--site=casu] [--catpath=] [--tempprefix=]
```

**Example usage**

```
# Querying the internet
wcsfit file.fits catalogue.fits --site cds

# Using a local catalogue
wcsfit file.fits catalogue.fits --catsrc localfits --catpath wcsfit-reference.fits
```

---

### `imstack`

`imstack` is used to stack to sum images in equatorial coordinates. We use this to build a deep stacked image to build the input catalogue. It requires the input images are astrometrically solved first otherwise the images will not align properly and the output will not be ideal.

Required input arguments are:

  * infiles - list of files to stack; the filename must be prepended with a @ a la iraf
  * confmaps - either list of confidence maps, or single confidence map
  * cats - extracted catalogues, or empty string
  * outfile - output stacked image
  * outconf - output confidence map

Typically we do not use any optional arguments.

```
Usage: imstack infiles confmaps cats outfile outconf
[--lthr=5] [--hthr=5] [--method=1] [--nplate=6] [--expkey=EXPTIME]
[--(no)seewt (no)] [--(no)magzptscl (no)]
```

