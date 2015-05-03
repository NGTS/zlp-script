#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import argparse
import logging
import shutil
from astropy.io import fits

logging.basicConfig(level='INFO', format='%(levelname)7s %(message)s')
logger = logging.getLogger(__name__)


def main(args):
    if args.verbose:
        logger.setLevel('DEBUG')
    logger.debug(args)

    logger.debug('Reading detrended flux')
    detrended_flux = fits.getdata(args.detrended, 1)['flux']
    detrended_hdu = fits.ImageHDU(detrended_flux, name='casudet')

    if args.output:
        logger.debug('Rendering to new file %s', args.output)
        with fits.open(args.photometry) as hdulist:
            hdulist.append(detrended_hdu)
            hdulist.writeto(args.output, clobber=True)
    else:
        logger.debug('Updating file %s', args.photometry)
        with fits.open(args.photometry, mode='update') as hdulist:
            hdulist.append(detrended_hdu)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--photometry', required=True, type=str)
    parser.add_argument('-d', '--detrended', required=True, type=str)
    parser.add_argument('-o', '--output', required=False, type=str)
    parser.add_argument('-v', '--verbose', action='store_true')
    main(parser.parse_args())
