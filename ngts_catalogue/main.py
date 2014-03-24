#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Zero Level Pipeline catalog generation

Usage:
  ZLP_create_cat [options] --confmap=CONFMAP --filelist=FILELIST

Options:
  -h --help                                 Show help text
  -v, --verbose                             Print more text
  -o <OUTNAME>, --outname <OUTNAME>         Specify the name of the output catalog [default: catfile.fits]
  -s <STACKLIST>, --stacklist <STACKLIST>   The name of the file that stores the names of the images used in the stack [default: stackfilelist]
  --c_thresh <C_THRESH>                     The detection threshold to use when defining the input [default: 2]
  --s_thresh <S_THRESH>                     The detection threshold to use when WCS solving images typically higher than when doing actual photometry [default: 7]
  -n <NPROC>, --nproc <NPROC>               Enable multithreading if you're analysing a lot of files at once
  -N <NFILES>, --nfiles <NFILES>            Maximum number of files to use in the stack
  --no-wcs                                  Do not solve each image for WCS.  However images must have a solution somehow
  --create-ell                              Produce ds9 region files for the final catalogue

This is the catalog generation tool, requires a filelist input. need to work on being selective on the files used in input.

"""

from docopt import docopt
import os
from .wcs_fitting import m_solve_images
from . import casutools
from .metadata import Metadata
from .ngts_logging import logger
from .version import __version__
from tempfile import NamedTemporaryFile
import sqlite3
from datetime import datetime

def main():
    argv = docopt(__doc__, version=__version__)
    if argv['--verbose'] == True:
        logger.enable_debug()

    start = datetime.now()

    # Pick the first N files if argument given
    nfiles = int(argv['--nfiles']) if argv['--nfiles'] else None
    logger.info('Creating source catalogue from first %s images...', nfiles)

    with NamedTemporaryFile() as tmp:
        name = tmp.name
        with open(argv['--filelist']) as infile:
            for i, line in enumerate(infile):
                if nfiles and i >= nfiles:
                    break

                _, cal_stat = line.strip('\n').split(' ')

                if cal_stat == 'ok':
                    tmp.write(line)

        tmp.seek(0)

        if not argv['--no-wcs']:
            logger.info("Astrometrically solving images")
            extracted_metadata = m_solve_images(name, name, thresh=argv['--s_thresh'],
                    nproc=int(argv['--nproc']) if argv['--nproc'] else None)
            Metadata(extracted_metadata).render()

        with open(argv['--stacklist'],'w') as stacklist:
            for line in tmp:
                image, _ = line.strip('\n').split(' ')

                status_check = line.strip('\n').split(' ')[1:]

                if all([status == 'ok' for status in status_check]):
                    stacklist.write(image + '\n')

    outstack_name = 'outstack.fits'
    outstackconf_name = 'outstackconf.fits'

    logger.info('Performing image stack')
    casutools.imstack(argv['--stacklist'], argv['--confmap'],
            outstack=outstack_name, outconf=outstackconf_name)
    logger.info('Extracting sources')
    casutools.imcore(outstack_name, argv['--outname'], threshold=argv['--c_thresh'],
            confidence_map=outstackconf_name,
            ellfile=argv['--create-ell'])

    logger.info('Catalogue complete')
    logger.info('Time taken: %s', datetime.now() - start)

if __name__ == '__main__':
    main()
