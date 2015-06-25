#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from astropy.io import fits

fname = sys.argv[1].strip()
header = fits.getheader(fname, 1)
assert header['zp'] == 0, "Zero point is %f, should be 0" % header['zp']
