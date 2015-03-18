from __future__ import print_function

import math
import sys
import os
import numpy as np
from astropy.io import fits as pyfits
from extract_overscan import extract_overscan

def render_total_file(data, fname, nfiles):
    hdu = pyfits.PrimaryHDU(data)
    hdu.header.set('nfiles', nfiles)
    hdu.writeto(fname)


inlist = str(sys.argv[1])
biasname = str(sys.argv[2])
darkname = str(sys.argv[3])
smname = str(sys.argv[4])
flatname = str(sys.argv[5])
outdir = str(sys.argv[6])+'/'

biasname = outdir+biasname
darkname= outdir+darkname
smname = outdir+os.path.basename(smname)
totalname = outdir+'flat_total.fits'
def reducer():
    os.system('mkdir '+outdir+'flats')
    hdulist = pyfits.open(biasname)
    bias = hdulist[0].data
    hdulist = pyfits.open(darkname)
    dark = hdulist[0].data    
    hdulist = pyfits.open(smname)
    sm = hdulist[0].data    
    os.system('rm -f '+outdir+'datafile.dat')
    os.system('rm -f '+outdir+'variance.fits')
    os.system('rm -f '+outdir+flatname)
    os.system('rm -f '+outdir+'std.fits')
    os.system('rm -f '+outdir+'expdata.dat')
    frameno = 1

    nflat_files = 0
    flat_total = np.zeros(dark.shape)
    datamatrix = []
    expfile = outdir+'expdata.dat'
    for line in file(inlist):
        stripped = line.strip()
        hdulist = pyfits.open(stripped)
        overscan = extract_overscan(hdulist)
        data = hdulist[0].data[0:2048,20:2068]
        exposure = hdulist[0].header['exposure']
        median_data = np.median(data[:, 20:-20])
        
        f = open(expfile, 'a')
        f.write(str(exposure)+'\n')
        f.close()

        to_include = (exposure >= 3) & (median_data < 40000)
        if not to_include:
            print("Skipping file {fname}, exptime={exptime}, med_data={med}"
                  .format(fname=stripped, exptime=exposure, med=median_data),
                  file=sys.stderr)
        else:

            corrected1 = (data-np.median(overscan)-bias-(dark*exposure))
            flat_total += corrected1
            nflat_files += 1
    
#        corrected2 = corrected1/(1-(sm/exposure))
            
            fmean = np.mean(corrected1)
            fstd = np.std(corrected1)

            normalised = corrected1/fmean
#        normalised = corrected1
            path, fname = os.path.split(stripped)
            outname = outdir+'flats/'+'proc'+fname
            dfile = outdir+'datafile.dat'
            f = open(dfile, 'a')
            f.write(str(frameno)+" "+str(fmean)+" "+str(fstd)+" "+str(exposure)+" "+outname)
            f.close()




            datamatrix.append(normalised)
        
     
        
            hdulist[0].data = normalised
            command = 'rm -f '+outname
            os.system(command)
            hdulist.writeto(outname)
            tfile = outdir+'processed.dat'
            f = open(tfile, 'a')
            f.write(outname)
            f.close()

            frameno += 1

    try:
        frame, means, stds = np.loadtxt(dfile, usecols = (0,1,2), unpack = True)
    except UnboundLocalError as err:
        if 'dfile' in str(err):
            raise RuntimeError("All flats invalid. Pipeline cannot continue"
                               ", original error: {}".format(str(err)))


    wholestd = np.std(datamatrix, axis=0)

    print(np.size(wholestd))
    
    hdulist[0].data = wholestd
    outname = outdir+'std.fits'
    hdulist.writeto(outname)
    print('std done')
    variance = 1/(wholestd*wholestd)

    hdulist[0].data = variance
    outname = outdir+'variance.fits'
    hdulist.writeto(outname)
    print('var done')
    flat = np.median(datamatrix, axis = 0)

    hdulist[0].data = flat

    outname = outdir+flatname
    hdulist.writeto(outname)
    print('flat done')

    render_total_file(flat_total, totalname, nflat_files)

if __name__ == '__main__':
    reducer()
