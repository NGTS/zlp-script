import math
import sys
import os
import numpy as np
from astropy.io import fits as pyfits
from extract_overscan import extract_overscan


inlist = str(sys.argv[1])
biasname = str(sys.argv[2])
darkname = str(sys.argv[3])
flatname = str(sys.argv[5])
caldir = str(sys.argv[6])+'/'
outdir = str(sys.argv[7])+'/'
biasname = caldir+biasname
darkname = caldir+darkname
flatname = caldir+flatname

os.system('rm -f '+outdir+'processed.dat')

def reducer():
    

    hdulist = pyfits.open(biasname)
    bias = hdulist[0].data
    hdulist = pyfits.open(darkname)
    dark = hdulist[0].data
    hdulist = pyfits.open(flatname)
    flat = hdulist[0].data    
    
    i = 1
    
    for line in file(inlist):
        stripped = line.strip('\n')
        hdulist = pyfits.open(stripped)
        overscan = extract_overscan(hdulist)
        data = hdulist[0].data[0:2048,20:2068]
        exposure = hdulist[0].header['exposure']
        corrected = (data-np.median(overscan)-bias-(dark*exposure))/flat
        path, fname = os.path.split(stripped)
        outname = outdir+'proc'+fname
        print outname
        hdulist[0].data = corrected
        hdulist[0].header.add_history('Overscan of '+str(np.median(overscan))+' subtracted')
        hdulist[0].header.add_history('Bias subtracted using '+str(biasname))
        hdulist[0].header.add_history('Dark subtracted using '+str(darkname))
        hdulist[0].header.add_history('Flat corrected using '+str(flatname))
        
        command = 'rm -f '+outname
        os.system(command)
        hdulist.writeto(outname)
        dfile = outdir+'processed.dat'
        f = open(dfile, 'a')
        f.write(outname)
        f.close()
        
        


reducer()
