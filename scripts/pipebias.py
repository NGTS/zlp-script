import math
import sys
import os
import numpy as np
from extract_overscan import extract_overscan
from pipeutils import open_fits_file
from astropy.io import fits

inlist = str(sys.argv[1])
biasname = str(sys.argv[2])
outdir = str(sys.argv[3])+'/'

os.system('rm -f '+outdir+'bsorted*')

def biasmaker():
    os.system('mkdir '+outdir)
    position = 0
    i = 1
    for line in file(inlist):
        fname = outdir+'bsorted'+"{0:03d}".format(position)
        f = open(fname, 'a')
        f.write(line)
        f.close()
        if i == 50:
            i = 0
            position += 1
        i += 1

    os.system('ls '+outdir+'bsorted* >removeindexlist.dat')


    i = 1

    for line in file('removeindexlist.dat'):

        datamatrix = []
        mastermatrix = []
        call = line.strip('\n')
        for line in file(call):
            line = line.strip()
            with open_fits_file(line) as hdulist:
                overscan = extract_overscan(hdulist)
                data = hdulist[0].data[0:2048,20:2068]
            corrected = data-np.median(overscan)
            datamatrix.append(corrected)
        print 'medianing'
        print np.shape(datamatrix)
        master = np.median(datamatrix, axis=0)
        print i
        mastermatrix.append(master)
        i += 1

    print 'averaging'
    print np.shape(mastermatrix)
    bias = np.mean(mastermatrix, axis=0)
    
    phdu = fits.PrimaryHDU(bias)
    outname = outdir+biasname
    command = 'rm -f '+outname
    os.system(command)
    phdu.writeto(outname)

    os.system('rm -f '+outdir+'bsorted* removeindexlist.dat')
biasmaker()
