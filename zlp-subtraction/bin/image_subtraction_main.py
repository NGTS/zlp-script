#!/usr/local/python/bin/python

import time
import os
import glob

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
from image_subtraction_singleimage import imagesubtraction

import multiprocessing
from multiprocessing import Pool
from multiprocessing import Process

import cPickle
import pickle

DIRECTORY     = os.getcwd()
DEBUG         = 0 # create additional output (1), save intermediate steps (2)
pythonpath = '/usr/local/python/bin'

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

def get_imagelist(imagelist,run):
    """Get Images from ASCII File"""
    dire, filename = os.path.split(imagelist)
    root, ext      = os.path.splitext(filename)
    if ext == '.fit':
        liste = [imagelist]
    else:
        liste = []
        f = open(imagelist, 'r')
        for image in f.xreadlines():
            liste.append(image)
    return(liste)

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

def create_fitstable(filename, idents):
    if DEBUG:
        print "| %20s ........ Create Fitstable" % (time.strftime("%Y-%m-%d %H:%M:%S"))
    if not os.path.exists(filename):
        fitsfile = filename
        hdu = pyfits.PrimaryHDU()
        hdulist = pyfits.HDUList([hdu])
        stars = len(idents)
        #table 1
        c1 = Column(name='OBJ_ID', format='A26', array=idents)
        # more columns if needed
        tbhdu = pyfits.new_table([c1])
        hdulist.append(tbhdu)
        # table 2
        c1 = Column(name='IMAGEID', format='A26')
        c2 = Column(name='JD', format='f8')
        # more columns if needed
        tbhdu = pyfits.new_table([c1,c2])
        hdulist.append(tbhdu)
        hdulist.writeto(filename)
    return(filename)
    
def read_inputcatalogue(catalogue):
  hdu = pyfits.open(catalogue)
  data = hdu[1].data
  return(data['Sequence_number'],data['Kron_flux'],data['Kron_flux_err'],data['Error_bit_flag'],data['X_coordinate'],data['Y_coordinate'])
 

def runsingleimage(command):
  k=os.system(command)
  return(k)
   
if __name__ == '__main__':
    workingdir   = sys.argv[1]
    reference    = sys.argv[2]
    imagelist    = sys.argv[3]
    starlist     = sys.argv[4]
    run          = sys.argv[5]
    processes    = sys.argv[6]
    r1           = sys.argv[7]
    r2           = sys.argv[8]
    installdir   = sys.argv[9]
    os.chdir(workingdir)

    if DEBUG:
        print sys.argv

    dire, filename = os.path.split(reference)
    refroot, ext   = os.path.splitext(filename)
    reftable= "%s/%s_%s_tbl.fits" % (dire, refroot, run)


    # get list of images
    if os.path.exists(imagelist):
        imagelist = get_imagelist(imagelist,run)
    else:
        string = "%20s Error file does not exist: %s \n " % (time.strftime("%Y-%m-%d %H:%M:%S"), imagelist)
        print string

    # get data from reference tabe
    fits=fitsio.FITS(reftable, 'r')
    idents = list(fits[1]['ID'][:])
    fits.close()
    del fits    
    # create output fitsfile
    if DEBUG:
      print "| %20s ........ Create Output file" % (time.strftime("%Y-%m-%d %H:%M:%S"))
    if not os.path.exists("%s/output/NGTS_ZLP_%s_%s.fits" % (workingdir,refroot, run)):
        if DEBUG:
            print "| %20s ........ file does not exist" % (time.strftime("%Y-%m-%d %H:%M:%S"))
        fitstable      = create_fitstable("%s/output/NGTS_ZLP_%s_%s.fits" % (workingdir,refroot, run), idents)
    else:
        if DEBUG:
            print "| %20s ........ Output file %s/output/NGTS_ZLP_%s_%s.fits already exists" % (time.strftime("%Y-%m-%d %H:%M:%S"),workingdir,refroot, run)
        fitstable = "%s/output/NGTS_ZLP_%s_%s.fits" % (workingdir,refroot, run)
        # add OBJ_ID if needed
        fits=fitsio.FITS(fitstable, 'rw')
        starids = list(fits[1]['OBJ_ID'][:])
        for sid in idents:
            if starids.count(sid) == 0:
                data = array([sid], dtype=[('OBJ_ID','S26')])
                fits[1].append(data)
        fits.close()
        del fits
        print "Output file %s already exists" % (fitstable)
    if DEBUG:
        print "| %20s ........Analyse Images" % (time.strftime("%Y-%m-%d %H:%M:%S"))
    pool = Pool(int(processes))
    argumentfile = "%s/output/NGTS_ZLP_%s.list" % (workingdir, run)
    arguments = []
    commands = []
    f = open("%s/output/NGTS_ZLP_%s.list" % (workingdir, run), 'w')
    for i in range(len(imagelist)):
        image = imagelist[i].rstrip()
        arguments.append([i+1,reference, image, starlist,int(float(r1)), int(float(r2)), workingdir, run,fitstable,reftable, installdir])
        f.write("%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s\n" % (i+1,reference, image, starlist,int(float(r1)), int(float(r2)), workingdir, run,fitstable,reftable, installdir))
        commands.append('%s/python %s/bin/image_subtraction_singleimage.py %s %d %s/output/NGTS_IS_%s_%s.p' % (pythonpath,installdir,argumentfile, i, workingdir,run, i))
    f.close()
    hdulist = pyfits.open(fitstable)
    starids = hdulist[1].data.field('OBJ_ID')
    hdulist.close()

    result = pool.imap(runsingleimage,commands)
    imageids=[]
    for i in range(len(imagelist)):
        print "Image (%6s/%6s)-------------------------------------"  % (i+1, len(imagelist))
#        try:
        if 1==1:
          ergebnis = result.next(timeout=3600)
          if ergebnis != 0:
             print "| %20s ERROR in processing........ next" % (time.strftime("%Y-%m-%d %H:%M:%S")) 
#        except:
#          print "| %20s ERROR........ next" % (time.strftime("%Y-%m-%d %H:%M:%S"))
#          continue
        print commands[i]
#        os.system(commands[i])

    pool.close()
    pool.terminate()
    del pool

    print "| %20s ........ Finish" % (time.strftime("%Y-%m-%d %H:%M:%S"))





            




















