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

    hdu_name = 'CASUDET'

    logger.info('Reading detrended magnitudes')
    with fits.open(args.detrended) as infile:
        data = infile[1].data
        header = infile[1].header

    zp = header['zp']
    logger.info('Converting with zero point %s', zp)

    bjd = data['bjd'][0]
    ind = np.argsort(bjd)
    detrended_magnitudes = data['flux'][:, ind]
    detrended_flux = mag_to_flux(detrended_magnitudes, zp=zp)
    detrended_hdu = fits.ImageHDU(detrended_flux, name=hdu_name)

    if args.output:
        logger.info('Rendering to new file %s', args.output)
        with fits.open(args.photometry) as hdulist:
            if hdu_name in hdulist:
                logger.warning('Removing old hdu: %s', hdu_name)
                del hdulist[hdu_name]
            hdulist.append(detrended_hdu)
            hdulist.writeto(args.output, clobber=True)
    else:
        logger.info('Updating file %s', args.photometry)
        with fits.open(args.photometry, mode='update') as hdulist:
            if hdu_name in hdulist:
                logger.warning('Removing old hdu: %s', hdu_name)
                del hdulist[hdu_name]
            hdulist.append(detrended_hdu)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--photometry', required=True, type=str)
    parser.add_argument('-d', '--detrended', required=True, type=str)
    parser.add_argument('-o', '--output', required=False, type=str)
    parser.add_argument('-v', '--verbose', action='store_true')
    main(parser.parse_args())
