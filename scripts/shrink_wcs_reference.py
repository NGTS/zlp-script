#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Usage:
    shrink.py [options] <file> (-b <bright> | --bright <bright>) (-f <faint> | --faint <faint>)

Options:
    -h, --help              Show this help
    -o, --output <output>   Output filename [default: shrunk.fits]
'''

import sys
import argparse
import numpy as np
import fitsio

def main(args):
    bright_limit = args.bright
    faint_limit = args.faint

    if bright_limit > faint_limit:
        bright_limit, faint_limit = faint_limit, bright_limit

    print "Filtering with limiting magnitude range {} to {}".format(bright_limit, faint_limit)

    with open(args.file) as infile:
        with fitsio.FITS(args.output, 'rw', clobber=True) as outfile:
            outfile.write(None)
            ra_vector, dec_vector, jmag_vector = [], [], []
            for i, line in enumerate(infile):
                if i == 0:
                    continue

                words = line.strip('\n').split()
                ra = float(words[0])
                dec = float(words[1])
                jmag = float(words[5])

                if (jmag > bright_limit) & (jmag < faint_limit):
                    ra_vector.append(ra)
                    dec_vector.append(dec)
                    jmag_vector.append(jmag)

            outfile.write({'ra': np.array(ra_vector), 'dec': np.array(dec_vector), 'jmag':
                           np.array(jmag_vector)})



if __name__ == '__main__':
    description = '''
    Shrink a casutools wcsfit-compatable catalogue to a specific magnitude range
    '''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('file')
    parser.add_argument('-b', '--bright', type=float, required=False,
                        help='Bright magnitude limit [default: 8]', default=8)
    parser.add_argument('-f', '--faint', type=float, required=False,
                        help='Faint magnitude limit [default: 14]', default=14)
    parser.add_argument('-o', '--output', type=str, required=True)
    main(parser.parse_args())

