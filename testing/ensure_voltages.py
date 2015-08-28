#!/usr/bin/env python
# -*- coding: utf-8 -*-


import argparse
from astropy.io import fits

def main(args):
    with fits.open(args.filename) as infile:
        imagelist_hdu = infile['imagelist']
        column_names = set([
            column.name for column in imagelist_hdu.columns])
        
    test_keys = ['VI_PLUS', 'VI_MINUS']
    for key in test_keys:
        assert key in column_names, 'Missing key: {}'.format(key)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    main(parser.parse_args())
