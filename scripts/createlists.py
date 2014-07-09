#!/usr/bin/env python

# Small python sxocript to create list of images for NGTS Zero-Level-Pipeline
# Output goes to Reduction Module
# Philipp Eigmueller Feb 6 2014

 
import glob
import pyfits
import os
import time
import sys

DIRECTORY = os.getcwd()
DEBUG = 0

def get_liste(directory, root, ext):
    ### search for all image files in the directories """
    liste = glob.glob("%s/%s*.%s" % (directory, root, ext))
    if DEBUG:
        print "| get_liste"
        print "| ",
        print "%s/%s*.%s" % (directory, root, ext)
    liste.sort()
    return(liste)


def sort_liste(liste, logroot, runnumber):
    ### Sort images for bias, darks, flats, and scientific frames"""
    biaslist = []
    darklist = []
    flatlist = []
    science  = []
    dithered = []
    for image in liste:
        hdulist = pyfits.open(image)
        imtype = hdulist[0].header['IMGTYPE']
        action = hdulist[0].header['ACTION']
        try:
            dither = hdulist[0].header['DITHER']
        except:
            dither = 'DISABLED'
        hdulist.close()
        string = "%20s %10s %30s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), imtype, image)
        result = write_log(logroot, runnumber, string, 2)
        if imtype == 'IMAGE':
            if action == 'observeFieldContinuous':
                if dither == 'ENABLED':
                    dithered.append(image)
                else:
                    science.append(image)
        elif imtype == 'DARK':
            darklist.append(image)
        elif imtype == 'BIAS':
            biaslist.append(image)
        elif imtype == 'FLAT':
            flatlist.append(image)
    string = "\n"
    string = string + "%20s %8d bias images identified\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), len(biaslist))
    string = string + "%20s %8d dark images identified\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), len(darklist))
    string = string + "%20s %8d flat images identified\n" % (time.strftime("%Y-%m-%d %H:%M:%S"),len(flatlist))
    string = string + "%20s %8d science images identified\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), len(science))
    string = string + "%20s \n" % (time.strftime("%Y-%m-%d %H:%M:%S"))
    string = string + "# ------------------------------------------------------\n"
    string = string + "# \n"
    result = write_log(logroot, runnumber, string, 1)
    result = write_log(logroot, runnumber, string, 2)
    return(biaslist, darklist, flatlist, science, dithered)


def sort_scilist(liste):
    fields = []
    scilists = []
    for item in liste:
        hdulist = pyfits.open(item)
        try:
            field = hdulist[0].header['OBJECT']
        except:
            field = hdulist[0].header['FIELD']
        hdulist.close()
        if fields.count(field) == 0:
            fields.append(field)
            scilists.append([])
        idx = fields.index(field)
        scilists[idx].append(item)
    return(fields,scilists)


def write_liste(liste, filename, logroot, runnumber):
    """ write output files """
    output = "%s/output/%s" % (DIRECTORY,filename)
    f = open(output, 'w')
    for item in liste:
        f.write("%s\n" % item)
    f.close()
    string = "%20s List written  (%4d entries) in file %40s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"),len(liste),output)
    write_log(logroot, runnumber, string, 1)
    write_log(logroot, runnumber, string, 2)
    return(0)


def write_log(logroot, runnumber, string, lognumber=2):
    if DEBUG:
        print "| Write_log"
        print "| ",
        print logroot, runnumber, string, lognumber
        print "|"
    if lognumber == 1:
        logtype = 'short'
    elif lognumber == 2:
        logtype = 'long'
       
    #f = open("%s/logfiles/%s_%s_%03d.log" % (DIRECTORY, logroot, logtype, runnumber), 'a')
    #f.write(string)
    #f.close()
    if lognumber == 1:
        print string
    return(0)


def check_log(logroot):
    runnumber = 1
    while os.path.exists("%s/logfiles/%s_short_%03d.log" % (DIRECTORY, logroot,runnumber)):
        runnumber += 1
    return(runnumber)


def write_logstart(directory, imageroot, ext, run, runnumber):
    if DEBUG:
        print "| write_logstart"
        print "| ",
        print directory, imageroot, ext, run, runnumber
        
    string =          "-------------------------------------------------\n"
    string = string + "%20s Creating lists of images for Zero Level pipeline\n " % (time.strftime("%Y-%m-%d %H:%M:%S"))
    string = string + "%20s using the script createlists.py\n " % (time.strftime("%Y-%m-%d %H:%M:%S"))
    string = string + "%20s \n " % (time.strftime("%Y-%m-%d %H:%M:%S"))
    string = string + "%20s All %s*.%s files in the directory \n " % (time.strftime("%Y-%m-%d %H:%M:%S"),imageroot,ext)
    string = string + "%20s %s \n " % (time.strftime("%Y-%m-%d %H:%M:%S"),directory)
    string = string + "%20s will be sorted.\n " %(time.strftime("%Y-%m-%d %H:%M:%S"))
    string = string + "%20s \n " % time.strftime("%Y-%m-%d %H:%M:%S")
    string = string + "%20s Working Directory is %s\n " % (time.strftime("%Y-%m-%d %H:%M:%S"),DIRECTORY)
    string = string + "%20s \n " % (time.strftime("%Y-%m-%d %H:%M:%S"))
    string = string + " -----------------------------------------------\n "
    string = string + "# \n "
    result = write_log(run, runnumber, string, 1)
    result = write_log(run, runnumber, string, 2)
    return(0)


if __name__ == '__main__':
   # SRW: strips quotation marks so this script can be submitted 
   #  as a queue job
   directory = sys.argv[1].replace('"', '')
   imageroot = sys.argv[2]
   ext       = sys.argv[3]
   run       = sys.argv[4]
   if DEBUG:
       print "----------------------------"
       print "| Main"
       print "| ",
       print directory, imageroot, ext, run
   runnumber = check_log(run)
   result = write_logstart(directory,  imageroot, ext, run, runnumber)
   liste = get_liste(directory, imageroot, ext)
   if DEBUG:
       print "----------------------------"
       print "| Main (2)"
       print "| ",
       print liste

   (biaslist,darklist,flatlist,sciencelist, ditherlist) = sort_liste(liste, run, runnumber)
   write_log(run, runnumber, "# \n",1)
   write_log(run, runnumber, "# \n",2)
   result = write_liste(biaslist, "%s_bias.list" % (run), run, runnumber)
   result = write_liste(darklist, "%s_dark.list" % (run), run, runnumber)
   result = write_liste(flatlist, "%s_flat.list" % (run), run, runnumber)
   fnames,scilists = sort_scilist(sciencelist)
   for i, field in enumerate(fnames):
       result = write_liste(scilists[i],"%s_image_%s.list" % (run, field), run, runnumber)
   fnames,ditlists = sort_scilist(ditherlist)
   for i, field in enumerate(fnames):
       result = write_liste(ditlists[i],"%s_dither_%s.list" % (run, field), run, runnumber)

   string = "# \n"
   string = string + "%20s Finished Job\n " % time.strftime("%Y-%m-%d %H:%M:%S")
   string = string + "# -----------------------------------------------\n "
   string = string + "\n"
   write_log(run, runnumber, string,1)
   write_log(run, runnumber, string,2)
