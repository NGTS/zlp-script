# -*- coding: utf-8 -*-

import os
import tempfile
from .catmatch import shift_wcs_axis, FailedToSolve
from .metadata import Metadata
from .ngts_logging import logger
from multiprocessing.dummy import Pool as ThreadPool
from functools import partial
import fitsio
import casutools

def ensure_valid_wcs(fname):
    with fitsio.FITS(fname, 'rw') as infile:
        hdu = infile[0]
        header = hdu.read_header()

        target = {
                'CTYPE1': 'RA---ZPN',
                'CTYPE2': 'DEC--ZPN',
                'PV2_1': 0.999993897433,
                'PV2_3': 8.11292725428,
                'PV2_5': 901.974288037,
                }

        for (key, value) in target.iteritems():
            if key not in header or header[key] != value:
                hdu.write_key(key, value)


def m_solve_images(filelist, outfile, nproc=None, thresh=20.0):
    infiles = []
    with open(filelist) as infile:
        for line in infile:
            parts = line.split()
            image = parts[0]
            status_checks = parts[1:]

            if all(status == 'ok' for status in status_checks):
                infiles.append(image)

    fn = partial(casu_solve, thresh=thresh)

    pool = ThreadPool(nproc)
    return pool.map(fn, infiles)

def casu_solve(casuin, thresh=20):
    with tempfile.NamedTemporaryFile(dir='.', suffix='.fits', prefix='catalogue.') as catfile:
        catfile_name = catfile.name

        ensure_valid_wcs(casuin)

        casutools.imcore(casuin, catfile_name, threshold=thresh)
        catfile.seek(0)

        # quick correction factor because the central wcs axis is not always pointed in the right place at the central distortion axis
        try:
            try:
                offsets = shift_wcs_axis(casuin, catfile_name)
            except IOError:
                logger.debug("Performing initial fit")
                casutools.wcsfit(casuin, catfile_name)
                offsets = shift_wcs_axis(casuin, catfile_name)
        except FailedToSolve as err:
            return Metadata.extract_failure_data(err, casuin, catfile_name)

        casutools.wcsfit(casuin, catfile_name)

        catfile.seek(0)
        return Metadata.extract_computed_data(casuin, catfile_name, offsets)
