#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from astropy.io import fits


def get_expected_sha():
    pass


def main():
    fname = sys.argv[1]

    pheader = fits.getheader(fname)

    expected = get_expected_sha()

    assert 'PIPESHA' in pheader, 'Cannot find key PIPESHA in header'

    sha = pheader['PIPESHA']


if __name__ == '__main__':
    main()
