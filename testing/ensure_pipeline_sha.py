#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from astropy.io import fits
import subprocess as sp


def get_expected_sha():
    cmd = ['git', 'rev-parse', 'HEAD']
    output = sp.check_output(cmd)
    return output.split()[0].strip()


def main():
    fname = sys.argv[1]

    pheader = fits.getheader(fname)

    max_key_length = 72
    expected = get_expected_sha()[:max_key_length]

    assert 'PIPESHA' in pheader, 'Cannot find key PIPESHA in header'

    sha = pheader['PIPESHA'][:max_key_length]

    assert sha == expected, '{} != {}'.format(sha, expected)


if __name__ == '__main__':
    main()
