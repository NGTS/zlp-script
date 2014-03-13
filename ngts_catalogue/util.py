# -*- coding: utf-8 -*-
from astropy import wcs
import fitsio

def load_wcs_from_file(filename,pixcrd):
    '''
    Load the WCS information from a fits header, and use it
    to convert pixel coordinates to world coordinates.
    '''
    # Parse the WCS keywords in the primary HDU
    w = wcs.WCS(fitsio.read_header(filename))

    # Convert pixel coordinates to world coordinates
    # The second argument is "origin" -- in this case we're declaring we
    # have 1-based (Fortran-like) coordinates.
    world = w.wcs_pix2world(pixcrd, 1)

    return world
