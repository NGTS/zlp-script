#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import argparse
import logging
import shutil
from astropy.io import fits
import numpy as np

logging.basicConfig(level='INFO', format='%(levelname)7s %(message)s')
logger = logging.getLogger(__name__)


def mag_to_flux(m, zp):
    return 10 ** ((zp - m) / 2.5)


def main(args):
    if args.verbose:
        logger.setLevel('DEBUG')
    logger.debug(args)

    hdu_name = 'TAMFLUX'

    with fits.open(args.tamuz) as infile:
        detflux_hdu = infile['flux']
        detflux_hdu.name = hdu_name

        logger.info('Updating file %s', args.photometry)
        with fits.open(args.photometry, mode='update') as hdulist:
            if hdu_name in hdulist:
                logger.warning('Removing old hdu: %s', hdu_name)
                del hdulist[hdu_name]
            hdulist.append(detflux_hdu)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--photometry', required=True, type=str)
    parser.add_argument('-t', '--tamuz', required=True, type=str)
    parser.add_argument('-v', '--verbose', action='store_true')
    main(parser.parse_args())

