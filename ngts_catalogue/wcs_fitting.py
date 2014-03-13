# -*- coding: utf-8 -*-

import os
import tempfile
from catmatch import shift_wcs_axis
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

def extract_image_data(filename):
    keys = ['PV2_1', 'PV2_3', 'PV2_5', 'CMD_RA', 'CMD_DEC',
            'TEL_RA', 'TEL_DEC', 'ACTIONID', 'EXPOSURE', 'CTS_MED', 'AIRMASS',
            'CD1_1', 'CD1_2', 'CD2_1', 'CD2_2', 'SKYLEVEL']

    with fitsio.FITS(filename) as infile:
        header = infile[0].read_header()
        header_items = {key.lower(): header[key] for key in keys}

    meta_items = {'filename': os.path.basename(filename)}

    return dict(header_items.items() + meta_items.items())

def extract_catalogue_data(filename):
    with fitsio.FITS(filename) as infile:
        return { 'nobj': infile[1].read_header()['naxis2'] }

def extract_computed_data(image_name, catalogue):
    '''
    Extract important header keywords and statistics of the solution
    '''
    image_data = extract_image_data(image_name)
    catalogue_data = extract_catalogue_data(catalogue)

    return dict(image_data.items() + catalogue_data.items())

def m_solve_images(filelist, outfile, nproc=None, thresh=20.0, verbose=False):
    infiles = []
    with open(filelist) as infile:
        for line in infile:
            parts = line.split()
            image = parts[0]
            status_checks = parts[1:]

            if all(status == 'ok' for status in status_checks):
                infiles.append(image)

    fn = partial(casu_solve, thresh=thresh, verbose=verbose)

    pool = ThreadPool(nproc)
    return pool.map(fn, infiles)

def casu_solve(casuin, thresh=20, verbose=False):
    with tempfile.NamedTemporaryFile(dir='.', suffix='.fits', prefix='catalogue.') as catfile:
        catfile_name = catfile.name

        ensure_valid_wcs(casuin)

        casutools.imcore(casuin, catfile_name, threshold=thresh, verbose=verbose)
        catfile.seek(0)

        # quick correction factor because the central wcs axis is not always pointed in the right place at the central distortion axis
        try:
            shift_wcs_axis(casuin, catfile_name, thresh=thresh)
        except IOError:
            print "Performing initial fit"
            casutools.wcsfit(casuin, catfile_name, verbose=verbose)
            shift_wcs_axis(casuin, catfile_name, thresh=thresh)

        casutools.wcsfit(casuin, catfile_name, verbose=verbose)

        catfile.seek(0)
        return extract_computed_data(casuin, catfile_name)
