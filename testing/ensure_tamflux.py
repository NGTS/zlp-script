#!/usr/bin/env python
# -*- coding: utf-8 -*-

from astropy.io import fits
import sys

fname = sys.argv[1]
with fits.open(fname) as infile:
    assert 'tamflux' in infile, "Cannot find HDU 'TAMFLUX'"
