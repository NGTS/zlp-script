#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 
Zero Level Pipeline apperture photometry 

Usage: 
  ZLP_app_photom [options] (-c <CONFMAP> | --confmap <CONFMAP>) (-C <CATFILE> | --catfile <CATFILE>) (-f <FILELIST> | --filelist <FILELIST> | INPUT ...)

Options:
  -h --help              Show help text
  --verbose              Print more text
  --dist=DISTMAP         The path to the relevent distortion 
  --outlist=OUTLIST      Specify the name of the list of completed files
  --nproc=NPROC          Enable multithreading if you're analysing a lot of files at once [default: 1]
  --apsize=APSIZE        The radius of the apperture you wish to use in the photometry stage [default: 2]
  --s_thresh=S_THRESH    The detection threshold to use when WCS solving images - typically higher than when doing actual photometry [default: 7]
  --catsrc=CATSRC        What catalogue to use during catalog matching [default: viz2mass]
  --catpath=CATPATH      If you're using a local catalog for cat matching, where is it? [default: False]
  --outdir=OUTDIR        Where you would like the result files to go [default: ./]

This is the apperture photometry portion of the pipeline. It can be driven either in a list mode
or on a single file
 
"""
from docopt import docopt
import sys
import linecache
from numpy import *
import threading
from os.path import isfile, join
from NGTS_workpackage import *
import pickle

argv = docopt(__doc__)

#if you don't provide an outlist name i'll assume you just want to add _phot to the end
if not argv['--outlist']:
  argv['--outlist'] = argv['<FILELIST>'] + '_phot'

outfile = open(argv['--outlist'],'w')
outfile.close()

#dist_map = {'CD2_1': -1.4191656988099457e-08, 'CD2_2': 0.0013885222778780631, 'RA_s': 0.055870512902160017, 'CD1_2': -1.8513409749920829e-07, 'CD1_1': 0.0013883723486931344, 'CRVAL2': 49.414386141920922, 'CRPIX1': 1002.0594111585548, 'CRPIX2': 982.11907123259516, 'CRVAL1': 285.95176591229813, 'PV2_1': 1.0, 'PV2_2': 0.0, 'PV2_3': 7.898207770193908, 'PV2_5': 1392.9968242630193, 'PV2_7': -265152.6479961705, 'DEC_s': 0.22189846295346452, 'CTYPE2': 'DEC--ZPN', 'CTYPE1': 'RA---ZPN'}

#test_map = '/ngts/pipedev/AperturePhot/test_map.p'

dist_map = pickle.load(open(argv['--dist'],'r'))

filelist = argv['<FILELIST>']
if filelist:
  m_solve_images(filelist,argv['--outlist'],dist_map,nproc=int(argv['--nproc']),thresh=int(argv['--s_thresh']),verbose=argv['--verbose'],catsrc=argv['--catsrc'],catpath=argv['--catpath'])
  m_wcs_photom(filelist,argv['--outlist'],int(argv['--apsize']),argv['<CONFMAP>'],argv['<CATFILE>'],nproc=int(argv['--nproc']),verbose=argv['--verbose'])

if argv['INPUT']:
  for filename in argv['INPUT']:
    casu_solve(filename,dist_map,argv['--s_thresh'],verbose=argv['--verbose'])
    casu_photom(filename,argv['<CONFMAP>'],argv['<CATFILE>'],argv['--apsize'],verbose=argv['--verbose'])
