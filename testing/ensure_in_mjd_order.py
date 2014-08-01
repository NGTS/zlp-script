#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import fitsio
import numpy as np

def main(fname):
    with fitsio.FITS(fname) as infile:
        tmid = infile['imagelist']['tmid'].read()

        if (tmid != np.sort(tmid)).all():
            sys.exit(1)


if __name__ == '__main__':
    main(sys.argv[1])
