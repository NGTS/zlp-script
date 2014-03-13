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
  --s_thresh <S_THRESH>                     The detection threshold to use when WCS solving images - typically higher than when doing actual photometry [default: 20]
  -n <NPROC>, --nproc <NPROC>               Enable multithreading if you're analysing a lot of files at once
  -N <NFILES>, --nfiles <NFILES>            Maximum number of files to use in the stack
  --no-wcs                                  Do not solve each image for WCS.  However images must have a solution somehow
  --create-ell                              Produce ds9 region files for the final catalogue

This is the catalog generation tool, requires a filelist input. need to work on being selective on the files used in input.

"""

from docopt import docopt
import os
from ngts_catalogue.wcs_fitting import m_solve_images
from ngts_catalogue import casutools
from tempfile import NamedTemporaryFile
import sqlite3

def main(argv):
    if argv['--verbose'] == True:
        print 'Creating source catalogue from first {} images...'.format(argv['--nfiles'])

    # Pick the first N files if argument given
    nfiles = int(argv['--nfiles']) if argv['--nfiles'] else None

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
            extracted_metadata = m_solve_images(name, name, thresh=argv['--s_thresh'],
                    nproc=int(argv['--nproc']) if argv['--nproc'] else None,
                    verbose=argv['--verbose'])

            with sqlite3.connect('metadata.sqlite') as connection:
                cursor = connection.cursor()
                cursor.execute('''create table metadata (
                id integer primary key,
                pv2_1 float,
                pv2_3 float,
                pv2_5 float,
                cd1_1 float,
                cd1_2 float,
                cd2_1 float,
                cd2_2 float,
                cmd_ra float,
                cmd_dec float,
                tel_ra float,
                tel_dec float,
                actionid integer,
                exposure float,
                cts_med float,
                airmass float,
                skylevel float,
                ra_offset float,
                dec_offset float,
                filename string
                )''')

                cursor.executemany('''insert into metadata (
                pv2_1,
                pv2_3,
                pv2_5,
                cd1_1,
                cd1_2,
                cd2_1,
                cd2_2,
                cmd_ra,
                cmd_dec,
                tel_ra,
                tel_dec,
                actionid,
                exposure,
                cts_med,
                airmass,
                skylevel,
                ra_offset,
                dec_offset,
                filename
                ) values (
                :pv2_1,
                :pv2_3,
                :pv2_5,
                :cd1_1,
                :cd1_2,
                :cd2_1,
                :cd2_2,
                :cmd_ra,
                :cmd_dec,
                :tel_ra,
                :tel_dec,
                :actionid,
                :exposure,
                :cts_med,
                :airmass,
                :skylevel,
                :ra_offset,
                :dec_offset,
                :filename)''', extracted_metadata)

        with open(argv['--stacklist'],'w') as stacklist:
            for line in tmp:
                image, _ = line.strip('\n').split(' ')

                status_check = line.strip('\n').split(' ')[1:]

                if all([status == 'ok' for status in status_check]):
                    stacklist.write(image + '\n')

    outstack_name = 'outstack.fits'
    outstackconf_name = 'outstackconf.fits'

    casutools.imstack(argv['--stacklist'], argv['--confmap'], verbose=argv['--verbose'],
            outstack=outstack_name, outconf=outstackconf_name)
    casutools.imcore(outstack_name, argv['--outname'], threshold=argv['--c_thresh'],
            confidence_map=outstackconf_name, verbose=argv['--verbose'],
            ellfile=argv['--create-ell'])

    if argv['--verbose'] == True:
        print 'Catalogue complete'

if __name__ == '__main__':
    main(docopt(__doc__))
