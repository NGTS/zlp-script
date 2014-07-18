#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
from datetime import datetime

import casutools
from .ngts_logging import logger
from .version import __version__

def main():
    argv = parse_args()
    if argv.verbose == True:
        logger.enable_debug()

    start = datetime.now()

    name = argv.filelist

    outstack_name = argv.outstack_name
    outstackconf_name = argv.outstackconf_name

    logger.info('Performing image stack')
    casutools.imstack(name, argv.confmap,
            outstack=outstack_name, outconf=outstackconf_name)
    logger.info('Extracting sources')
    casutools.imcore(outstack_name, argv.outname, threshold=argv.c_thresh,
            confidence_map=outstackconf_name,
            ellfile=argv.create_ell)

    logger.info('Catalogue complete')
    logger.info('Time taken: %s', datetime.now() - start)

def parse_args():
    outname_default = 'catfile.fits'
    nproc_default = 1
    c_thresh_default = 7
    outstack_name_default = 'outstack.fits'
    outstackconf_name_default = 'outstackconf.fits'

    description = 'Zero Level Pipeline catalog generation'
    epilog = """This is the catalog generation tool, requires a filelist input.
    need to work on being selective on the files used in input."""

    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument('--confmap', required=True, type=str, help='Confidence map')
    parser.add_argument('--filelist', required=True, type=str, help='Filelist')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='Print more text')
    parser.add_argument('-o', '--outname', required=False, default=outname_default, type=str,
                        help='Specify the name of the output catalog [default: {}]'.format(
                        outname_default))
    parser.add_argument('--c_thresh', required=False, default=c_thresh_default, type=float,
                        help='The detection threshold to use when defining the input catalogue '
                        '[default: {}]'.format(c_thresh_default))
    parser.add_argument('-n', '--nproc', required=False, default=nproc_default, type=int,
                        help='Number of processors to use [default: {}]'.format(nproc_default))
    parser.add_argument('--outstack-name', required=False, default=outstack_name_default,
                        type=str,
                        help='Output stack file name [default: {}]'.format(outstack_name_default))
    parser.add_argument('--outstackconf-name', required=False, type=str,
                        default=outstackconf_name_default,
                        help='Output confidence map name [default: {}]'.format(
                            outstackconf_name_default))
    parser.add_argument('--create-ell', action='store_true', default=False,
                        help='Create a ds9 region file')
    return parser.parse_args()

if __name__ == '__main__':
    main()
