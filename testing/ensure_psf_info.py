#!/usr/bin/env python
# -*- coding: utf-8 -*-

from astropy.io import fits
import argparse

def main(args):
    imagelist = fits.getdata(args.filename, 'imagelist')
    column_names = set(key.lower() for key in imagelist.columns.names)

    required_keys = ['psf_a_5', 'psf_b_5']

    for key in required_keys:
        assert key in column_names, 'Cannot find key {}'.format(key)
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    main(parser.parse_args())
