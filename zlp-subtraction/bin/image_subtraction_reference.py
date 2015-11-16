#!/usr/local/python/bin/python

import os
import glob
import time
import sys

from numpy import *
import math
import pyfits
from pyfits import Column
import scipy
import scipy.ndimage
import scipy.ndimage.filters
import numpy
import numpy.linalg
import fitsio


DIRECTORY     = os.getcwd()
DEBUG         = False 

def file_delete(filename,run):
    """Delete File"""
    if os.path.exists(filename):
        os.remove(filename)
        string = "%20s Delete File %s \n " % (time.strftime("%Y-%m-%d %H:%M:%S"),filename)
        write_log(run, string, 2)
    return(0)

def write_log(logroot,string, lognumber=2):
    """Write additional Information into Log File"""
    if lognumber == 1:
        logtype = 'short'
    elif lognumber == 2:
        logtype = 'long'
    f = open("%s/logfiles/%s_%s.log" % (DIRECTORY, logroot, logtype), 'a')
    f.write(string)
    f.close()
    return(0)

#

def get_background(stamp, mask):
    bg=zeros(8)
    for i in range(len(bg)):
        condlist  = [mask==(i+2)]
        bgmask    = select(condlist,[stamp])
        bgmask    = bgmask.flatten()
        condition = bgmask != 0
        bgmask    = compress(condition, bgmask)
        bg[i]     = median(bgmask)
    mbg     = bg.mean() #first guess
    sigma   = bg.std() 
    diff = 9999
    counter = 0
    converge = 0
    while diff > 0.01:
        counter += 1
        oldsky = mbg
        w      = 1./exp(pow((bg-mbg),2)/sigma)
        sky    = (w*bg).sum()/w.sum() 
        diff = abs(sky-oldsky)/oldsky
        mbg = sky
        if counter > 50:
            print "| %20s ........ BG did not converge" % (time.strftime("%Y-%m-%d %H:%M:%S"))
            converge =1
            break
    return(mbg, sigma, converge)

def aperturemask(halfstampsize, r1, r2):
    """Create Aperture Mask"""
    stamp = zeros((halfstampsize*2+1,halfstampsize*2+1),int)
    for i in range(int(halfstampsize*2+1)):
      for j in range(int(halfstampsize*2+1)):
          x = halfstampsize-i
          y = halfstampsize-j
          if (sqrt(x*x+y*y) <= r1):
              stamp[i][j]=1
          elif (sqrt(x*x+y*y) > r1) and (sqrt(x*x+y*y) <= r2):
              if x <= 0: # down                                                                                                                   
                  if y < 0: #right                                                                                                                     
                      if abs(x) >= abs(y):
                          stamp[i][j] = 5
                      else:
                          stamp[i][j] = 4
              if x < 0: # down                                                                                                                   
                  if y >= 0: #left                                                                                                                  
                      if abs(x) > abs(y):
                          stamp[i][j] = 6
                      else:
                          stamp[i][j] = 7
              if x > 0: #up                                                                                                                    
                  if y <= 0: #right                                                                                                                     
                      if abs(x) > abs(y):
                          stamp[i][j] = 2
                      else:
                          stamp[i][j] = 3
              if x >= 0: #up                                                                                                                    
                  if y > 0: #left                                                                                                                  
                      if abs(x) >= abs(y):
                          stamp[i][j] = 9
                      else:
                          stamp[i][j] = 8
    return(stamp)

def get_photometry(image, starlist):
    print "Get Photometry"
    hdulist   = pyfits.open(image)
    dire,filename = os.path.split(image)
    root,ext = os.path.splitext(filename)
    imagedata = hdulist[0].data
    hdulist.close()
    hdustars = pyfits.open(starlist)
    stardata = hdustars[1].data
    starcount = len(hdustars[1].data['X_coordinate'])
    flc = zeros(starcount)
    flc[:]=NaN
    elc = zeros(starcount)
    elc[:]=NaN
    flag = zeros(starcount)
    idents = []
    xs   = hdustars[1].data.field('X_coordinate')
    ys   = hdustars[1].data.field('Y_coordinate')
    radius = hdustars[1].data.field('Kron_radius')
    r1 = math.ceil(radius.mean()+radius.std())
    r2 = math.ceil(r1*2.5)
    mask = aperturemask(r2, r1, r2)
    for i in range(starcount):
        x = xs[i]
        y = ys[i]
        idents.append("%s_%s" % (x,y))
        if ((x<r2+1) or (x > len(imagedata[0])-r2)):
            i+=1
            continue
        if ((y<r2+1) or (y > len(imagedata)-r2)):
            i+=1
            continue
        stamp      = imagedata[(int(y-0.5)-r2):(int(y-0.5)+r2+1),(int(x-0.5)-r2):(int(x-0.5)+r2+1)]
        bg, sigma, check  = get_background(stamp, mask)
        stamp      = stamp - bg
        condlist   = [mask==1]
        fluxmask   = select(condlist, [stamp])
        flc[i]     = ma.masked_invalid(fluxmask).sum()
        condlist   = [mask==1]
        fluxmask   = select(condlist, [stamp])
        flc[i]     = fluxmask.sum()
        elc[i]     = sqrt(pow(len(fluxmask.flatten()),2)*sigma+flc[i])/flc[i]
        flag[i]    = check
        i += 1
    return(idents,flc,elc, flag,xs,ys)

def save_referencetable(reference, idents, flux, error,flag,xs,ys, run):
    dire, filename = os.path.split(reference)
    root, ext = os.path.splitext(filename)
    tablename = "%s/%s_%s_tbl.fits" % (dire, root, run)
    c1 = Column(name='ID', format='A26', array=idents)
    c2 = Column(name='Counts', format='J', array=flux)
    c3 = Column(name='Errors', format='D', array=error)
    c4 = Column(name='Flag', format='L', array=flag)
    c5 = Column(name='X_coordinate', format='D', array=xs)
    c6 = Column(name='Y_coordinate', format='D', array=ys)
    tbhdu = pyfits.new_table([c1, c2, c3, c4,c5,c6])
    tbhdu.writeto(tablename)
    return(tablename)
    
    

if __name__ == '__main__':
    workingdir   = sys.argv[1]
    frame        = sys.argv[2]
    catalogue    = sys.argv[3]
    run          = sys.argv[4]
    os.chdir(workingdir)
    if DEBUG:
        print sys.argv

    # create reference table
    dire, filename = os.path.split(frame)
    refroot, ext   = os.path.splitext(filename)
    if not os.path.exists("%s/%s_%s_tbl.fits" % (dire, refroot, run)):
        print "Reference Table %s/%s_%s_tbl.fits will be created" % (dire, refroot, run)
        idents, rlc, elc,flag,xs,ys = get_photometry(frame, catalogue)
        reftable       = save_referencetable(frame, idents, rlc, elc,flag,xs,ys, run)
    else:
        reftable = "%s/%s_%s_tbl.fits" % (dire, refroot, run)
        print "Reference Table %s/%s_%s_tbl.fits already exists" % (dire, refroot, run)





            




















