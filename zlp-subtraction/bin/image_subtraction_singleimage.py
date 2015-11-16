#!/usr/local/python/bin/python

import os
import glob
import time
import sys
from   numpy import *
import math
import shutil
import pyfits
from   pyfits import Column
import scipy
import scipy.ndimage
import scipy.ndimage.filters
import numpy
import numpy.linalg
import fitsio
from astropy.io import fits
from reproject import reproject_interp
#from reproject import reproject_exact
import subprocess

import cPickle
import pickle

DIRECTORY     = os.getcwd()
DEBUG         = False # create additional output (1), save intermediate steps (2)

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
            if DEBUG:
              print "| %20s ........ BG did not converge" % (time.strftime("%Y-%m-%d %H:%M:%S"))
            converge =1
            break
    return(mbg, sigma, converge)

def aperturemask(halfstampsize, r1, r2):
    """Create Aperture Mask"""
    stamp = zeros((halfstampsize*2+1,halfstampsize*2+1),int)
    for i in range(halfstampsize*2+1):
      for j in range(halfstampsize*2+1):
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

def get_photometry(image, starlist, r1, r2):
    mask = aperturemask(r2, r1, r2)

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
    rlc  = hdustars[1].data.field('Counts')
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
        elc[i]     = sqrt(pow(len(fluxmask.flatten()),2)*sigma+flc[i])/abs(flc[i])
        flag[i]    = check
        sys.stdout.flush()
        i += 1
    return(idents,flc,elc, flag,xs,ys,rlc)


def alignimage(reference, image, outfile, exact='True', order='nearest-neighbor'):
  hdu1 = fits.open(reference)[0]
  hdu2 = fits.open(image)[0]
  newheader = hdu2.header
  wcsheaderitems=['WCSPASS', \
                  'WCSF_NS', \
                  'WCSF_RMS', \
                  'WCSF_RA', \
                  'WCSF_DEC', \
                  'WCSCOMPL', \
                  'PV2_1', \
                  'PV2_2', \
                  'PV2_3', \
                  'PV2_5', \
                  'PV2_7', \
                  'DEC_S', \
                  'RA_S', \
                  'CTYPE1', \
                  'CTYPE2', \
                  'CRVAL1', \
                  'CRVAL2', \
                  'CRPIX1', \
                  'CRPIX2', \
                  'CD1_1', \
                  'CD2_2', \
                  'CD1_2', \
                  'CD2_1']
  for item in wcsheaderitems:
    try:
      newheader[item]=hdu1.header[item]
    except:
      if DEBUG:
        print "%s: header entry %s not set" % (image,item)
  if not exact:
    array, footprint = reproject_interp(hdu2, hdu1.header, order=order)
  else:
    array, footprint = reproject_exact(hdu2, hdu1.header, parallel=False)
    print array[1000]
    print footprint[1000]
  dire, filename = os.path.split(outfile)
  root,ext = os.path.splitext(filename)
  fits.writeto(outfile, array, newheader, clobber=True)
  if DEBUG:
    fits.writeto("%s/%s_fp.fits" % (dire,root), footprint, newheader, clobber=True)
  return(0)

def imagesubtraction(parameters):
    imag, reference, image, starlist,r1, r2, workingdir, run,fitstable,reftable, installdir = parameters
    imag = imag.strip()
    reference = reference.strip()
    image =image.strip()
    r1 = int(r1)
    r2 = int(r2)
    workingdir = workingdir.strip()
    run = run.strip()
    fitstable = fitstable.strip()
    reftable = reftable.strip()
    installdir = installdir.strip()
    # Align image
    imagedir, imagefile = os.path.split(image)
    imageroot = os.path.splitext(imagefile)[0]

    saveout = sys.stdout
    saveerr = sys.stderr
    logfile = open("%s/logfiles/%s_long.log" % (workingdir, run), 'a')
    sys.stdout = logfile
    sys.stderr = logfile
    print ""
    print ""
    print "-------------------------------------"
    print "|"
    print "| %s %s RUN Image Subtraction" % (imag, imageroot)


    
    alignimage(reference, image, '%s/output/interp_%s' % (workingdir, imagefile), exact=False, order='bilinear')
#    alignimage(reference, image, '%s/output/interp-nearest_neighbor_%s' % (workingdir, imagefile), exact=False, order='nearest-neighbor')
#    alignimage(reference, image, '%s/output/interp-biquadratic_%s' % (workingdir, imagefile), exact=False, order='biquadratic')
#    alignimage(reference, image, '%s/output/interp-bicubic_%s' % (workingdir, imagefile), exact=False, order='bicubic')
#    alignimage(reference, image, '%s/output/interp-bilinear_%s' % (workingdir, imagefile), exact=False, order='bilinear')
#    alignimage(reference, image, '%s/output/interp-exact_%s' % (workingdir, imagefile), exact=True)

    # copy config files
    configfiles = glob.glob('%s/config/default_*' % installdir)
    if not os.path.exists("%s/config" % workingdir):
      os.mkdir("%s/config" % workingdir)
    for item in configfiles:
      filename = os.path.split(item)[1] 
      shutil.copyfile(item, "%s/config/%s" % (workingdir,filename))
    if not os.path.exists('%s/logfiles' % workingdir):
      os.mkdir('%s/logfiles' % workingdir)
    os.chdir("%s/output" % workingdir)

#    command = ' %s/bin/mrj_phot %s %s/output/interp-biquadratic_%s -c %s/config/default_config >> %s/logfiles/%s_long.log 2>>  %s/logfiles/%s_long.log'  % (installdir, reference, workingdir, imagefile, workingdir,workingdir, run, workingdir, run)
#    antwort = os.system(command)
#    command = ' %s/bin/mrj_phot %s %s/output/interp-bicubic_%s -c %s/config/default_config >> %s/logfiles/%s_long.log 2>>  %s/logfiles/%s_long.log'  % (installdir, reference, workingdir, imagefile, workingdir,workingdir, run, workingdir, run)
#    antwort = os.system(command)
#    command = ' %s/bin/mrj_phot %s %s/output/interp-bilinear_%s -c %s/config/default_config >> %s/logfiles/%s_long.log 2>>  %s/logfiles/%s_long.log'  % (installdir, reference, workingdir, imagefile, workingdir,workingdir, run, workingdir, run)
#    antwort = os.system(command)
#    command = ' %s/bin/mrj_phot %s %s/output/interp-exact_%s -c %s/config/default_config >> %s/logfiles/%s_long.log 2>>  %s/logfiles/%s_long.log'  % (installdir, reference, workingdir, imagefile, workingdir,workingdir, run, workingdir, run)
#    antwort = os.system(command)
#    command = ' %s/bin/mrj_phot %s %s/output/interp-nearest_neighbor_%s -c %s/config/default_config >> %s/logfiles/%s_long.log 2>>  %s/logfiles/%s_long.log'  % (installdir, reference, workingdir, imagefile, workingdir,workingdir, run, workingdir, run)
#    antwort = os.system(command)
    
    if not os.path.exists("%s/output/interp_%s" % (workingdir, imagefile)):
        print "| %s " % imageroot,
        print "File %s/output/interp_%s does not exist"  % (workingdir, imagefile)

    command = '/home/philipp/bin/mrj_phot %s %s/output/interp_%s -c %s/config/default_config >>%s/logfiles/%s_long.log 2>>%s/logfiles/%s_long.log'  % (installdir, reference, workingdir, imagefile, workingdir, workingdir, run,workingdir, run)
    command = '/home/philipp/bin/mrj_phot'  % (installdir)

    subtract = subprocess.Popen((command, '%s' % reference, '%s/output/interp_%s' % (workingdir, imagefile), '-c', '%s/config/default_config' % ( workingdir)), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = subtract.communicate()
#    antwort = os.system(command)

    if os.path.exists("%s/output/conv_interp_%s" % (workingdir,imagefile)):
        subtracted = "%s/output/conv_interp_%s" % (workingdir,imagefile)
    else:
        string = "|  8 %20s ERROR running ISIS on interp_%s \n " % (time.strftime("%Y-%m-%d %H:%M:%S"), imagefile)
        print "| %s " % imageroot,
        print command
        print "| %s " % imageroot,
        print string
        return([-1], [-1], [-1], [-1], [-1], [-1], [-1], [-1], [-1], [-1])
    file_delete("%s/output/kt_%s" % (workingdir,imagefile), run)
    file_delete("%s/output/kc_0interp_%s" % (workingdir,imagefile), run)
    file_delete("%s/output/refconv_interp_%s" % (workingdir,imagefile), run)
    print "| %s " % imageroot,
    print "%20s ........Photometry" % (time.strftime("%Y-%m-%d %H:%M:%S"))
    idents,flc,elc, flag,xs,ys,rlc = get_photometry(subtracted, reftable, r1,r2)
    condition = (isnan(flc) == False)
    flc[condition] = rlc[condition]-flc[condition]
    if DEBUG:
        print image

    hdulist = pyfits.open(image)
    hdr = hdulist[0].header
    date = float(hdr['MJD'])
    imageid= '%s_%s' % (date,imageroot)
    hdulist.close()
    indices = array(range(len(idents)))
    print "| %s " % imageroot,
    print "Photometry on image %s finished with success" % image
    sys.stdout = saveout
    sys.stderr = saveerr

    logfile.close()
    if not DEBUG:
      file_delete('%s/output/interp_%s' % (workingdir,imagefile))
      file_delete(subtracted)


    return(idents, flc, elc, flag,xs,ys,rlc,imageid,date,indices)



if __name__ == '__main__':
  print sys.argv
  f = open(str(sys.argv[1]), 'r')
  parameters = []
  for line in f.xreadlines():
    line = line.strip()
    parameters.append(line.split(','))
#  parameters = cPickle.load(f)
#  f.close()
  index = int(sys.argv[2])
  parameters = parameters[index]
  results = imagesubtraction(parameters)  
  f = open(sys.argv[3], 'wb')
  cPickle.dump(results, f) 
  f.close()         






















