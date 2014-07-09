import math
import sys
import os
import numpy as np
import pyfits
import matplotlib.pyplot as plt

inlist = str(sys.argv[1])
biasname = str(sys.argv[2])
darkname = str(sys.argv[3])
smname = str(sys.argv[4])
flatname = str(sys.argv[5])
outdir = str(sys.argv[6])+'/'

biasname = outdir+biasname
darkname= outdir+darkname
smname = outdir+smname
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

    datamatrix = []
    expfile = outdir+'expdata.dat'
    for line in file(inlist):
        stripped = line.strip('\n')
        hdulist = pyfits.open(stripped)
        overscan = hdulist[0].data[0:2048,0:19]
        data = hdulist[0].data[0:2048,20:2068]
        exposure = hdulist[0].header['exposure']
        
        f = open(expfile, 'a')
        f.write(str(exposure)+'\n')
        f.close()
        if (exposure >= 1):

            corrected1 = (data-np.median(overscan)-bias-(dark*exposure))
    
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

    frame, means, stds = np.loadtxt(dfile, usecols = (0,1,2), unpack = True)

#    plt.hist(means)
#    plt.xlabel('Mean Counts')
#    plt.show()
    
#    plt.hist(stds)
#    plt.xlabel('Stddev')
#    plt.show()

    wholestd = np.std(datamatrix, axis=0)

    print np.size(wholestd)
    
    hdulist[0].data = wholestd
    outname = outdir+'std.fits'
    hdulist.writeto(outname)
    print 'std done'
    variance = 1/(wholestd*wholestd)

    hdulist[0].data = variance
    outname = outdir+'variance.fits'
    hdulist.writeto(outname)
    print 'var done'
    flat = np.median(datamatrix, axis = 0)

    hdulist[0].data = flat

    outname = outdir+flatname
    hdulist.writeto(outname)
    print 'flat done'

reducer()
