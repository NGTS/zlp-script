#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Usage:
    shrink.py [options] <file> (-b <bright> | --bright <bright>) (-f <faint> | --faint <faint>)

Options:
    -h, --help              Show this help
    -o, --output <output>   Output filename [default: shrunk.fits]
'''

import fitsio
import sys
import argparse

def main(args):
    bright_limit = args.bright
    faint_limit = args.faint

    if bright_limit > faint_limit:
        bright_limit, faint_limit = faint_limit, bright_limit

    print "Filtering with limiting magnitude range {} to {}".format(bright_limit, faint_limit)

    with fitsio.FITS(args.file) as infile:
        with fitsio.FITS(args.output, 'rw', clobber=True) as outfile:
            for hdu in infile:
                print '---'
                print "HDU '{}'".format(hdu.get_extname())
                if hdu.get_exttype() == 'ASCII_TBL' or hdu.get_exttype() == 'BINARY_TBL':
                    print "Ascii table found"
                    data = hdu.read()

                    n_before = len(data)
                    print "Found {} objects".format(n_before)

                    ind = (data['Jmag'] >= float(bright_limit)) & (data['Jmag'] < float(faint_limit)) 
                    if not ind.any():
                        raise RuntimeError("No objects included")

                    new_data = data[ind]
                    n_after = len(new_data)
                    print "Accepting {} objects".format(n_after)
                    outfile.write(new_data)
                else:
                    print "Other table type found"
                    outfile.write(hdu.read())



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

