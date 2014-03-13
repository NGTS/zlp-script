# -*- coding: utf-8 -*-
import os
from astropy.io import fits as pf
import fitsio
from util import load_wcs_from_file
from numpy import *
import os

def shift_wcs_axis(casuin,mycatname,thresh=100):

    #this is the best solution for the catalog
    CRPIX1  =  -30.3589661445
    CRPIX2  =  -1.76800252831
    CRVAL1  =  -0.0134278702942
    CRVAL2  =  -0.0444093066511
    CD1_1   =  0.00138877871593
    CD2_2   =  0.00138875543313
    CD1_2   =  1.41054781057e-05
    CD2_1   =  -1.41656423353e-05
    PV2_1   =  0.999993897433
    PV2_3   =  8.11292725428
    PV2_5   =  901.974288037

    with fitsio.FITS(casuin) as hdulist:
        header = hdulist[0].read_header()
        XVAL = header['NAXIS1']/2
        YVAL = header['NAXIS2']/2
        TEL_RA = header['TEL_RA']
        TEL_DEC = header['TEL_DEC']

    prior = [CRPIX1,CRPIX2,CRVAL1,CRVAL2,CD1_1,CD2_2,CD1_2,CD2_1,PV2_1,PV2_3,PV2_5]

    apply_correct(prior,casuin,XVAL,YVAL,TEL_RA,TEL_DEC)

    # this corrects efficiently for the 'offset' between the optical axis and the RA/DEC optical axis
    xs,ys,RA_sep,DEC_sep, sep_list = calc_seps(mycatname,casuin)

    median_ra_offset = median(RA_sep)
    median_dec_offset = median(DEC_sep)
    prior[2] += median_ra_offset
    prior[3] += median_dec_offset

    apply_correct(prior,casuin,XVAL,YVAL,TEL_RA,TEL_DEC)
    return {'ra_offset': median_ra_offset, 'dec_offset': median_dec_offset}

def apply_correct(x,casuin,XVAL,YVAL,TEL_RA,TEL_DEC):

    with fitsio.FITS(casuin, 'rw') as fits:
        hdu = fits[0]
        hdu.write_key('CRPIX1', XVAL + x[0])
        hdu.write_key('CRPIX2', YVAL + x[1])
        hdu.write_key('CRVAL1', TEL_RA + x[2])
        hdu.write_key('CRVAL2', TEL_DEC + x[3])
        hdu.write_key('CD1_1', x[4])
        hdu.write_key('CD2_2', x[5])
        hdu.write_key('CD1_2', x[6])
        hdu.write_key('CD2_1', x[7])
        if len(x) > 8:
                hdu.write_key('PV2_1', x[8])
                hdu.write_key('PV2_3', x[9])
                hdu.write_key('PV2_5', x[10])

    
def calc_seps(mycatname,casuin):


    plate_scale = -3600.0/5.0

    cat_names = []
    RA_lims = []
    DEC_lims = []
    for line in open('catcache/index'):
            vals = line.strip('\n').split(' ')
            cat_names += [vals[0]]
            RA_lims += [[float(vals[2]),float(vals[3])]]
            DEC_lims += [[float(vals[4]),float(vals[5])]]

    n = 0

    cat_name = cat_names[n]
    with pf.open('catcache/' + cat_name) as cat:
        cat_RA_raw = cat[1].data['ra']
        cat_DEC_raw = cat[1].data['dec']
        cat_Jmag = cat[1].data['Jmag']

    zero = 21.5

    with fitsio.FITS(mycatname) as mycat:
        hdu = mycat[1]

        keys = ['x_coordinate', 'y_coordinate', 'Aper_flux_3']
        data = hdu[keys]
        my_flux, my_X, my_Y = [data[key][:] for key in keys]
        my_mag = zero - 2.512*log10(my_flux)

    pix_coords = [[my_X[i],my_Y[i]] for i in range(0,len(my_X))]

    world = load_wcs_from_file(casuin,pix_coords)

    my_RA_raw = world[:,0]
    my_DEC_raw = world[:,1]

    sep_list = []
    DEC_sep = []
    RA_sep = []
    xs = []
    ys = []
    x_sep = []
    y_sep = []

    try:
        my_RA = my_RA_raw[(my_RA_raw > RA_lims[n][0]) & (my_RA_raw < RA_lims[n][1]) & (my_DEC_raw > DEC_lims[n][0]) & (my_DEC_raw < DEC_lims[n][1])]
        my_DEC = my_DEC_raw[(my_RA_raw > RA_lims[n][0]) & (my_RA_raw < RA_lims[n][1]) & (my_DEC_raw > DEC_lims[n][0]) & (my_DEC_raw < DEC_lims[n][1])]
        cat_RA = cat_RA_raw[(cat_RA_raw > min(my_RA)) & (cat_RA_raw < max(my_RA)) & (cat_DEC_raw > min(my_DEC)) & (cat_DEC_raw < max(my_DEC))]
        cat_DEC = cat_DEC_raw[(cat_RA_raw > min(my_RA)) & (cat_RA_raw < max(my_RA)) & (cat_DEC_raw > min(my_DEC)) & (cat_DEC_raw < max(my_DEC))]
    except:
        return xs,ys,RA_sep,DEC_sep, array([10.0])

    my_X = my_X[(my_RA_raw > RA_lims[n][0]) & (my_RA_raw < RA_lims[n][1]) & (my_DEC_raw > DEC_lims[n][0]) & (my_DEC_raw < DEC_lims[n][1])]
    my_Y = my_Y[(my_RA_raw > RA_lims[n][0]) & (my_RA_raw < RA_lims[n][1]) & (my_DEC_raw > DEC_lims[n][0]) & (my_DEC_raw < DEC_lims[n][1])]

    my_brightest = argsort(my_mag[(my_RA_raw > RA_lims[n][0]) & (my_RA_raw < RA_lims[n][1]) & (my_DEC_raw > DEC_lims[n][0]) & (my_DEC_raw < DEC_lims[n][1])])[:20]

    c_b = argsort(cat_Jmag[(cat_RA_raw > min(my_RA)) & (cat_RA_raw < max(my_RA)) & (cat_DEC_raw > min(my_DEC)) & (cat_DEC_raw < max(my_DEC))])[:100]

    for i in my_brightest:
        RA = my_RA[i]
        DEC = my_DEC[i]
        sep = 3600*(((RA - cat_RA[c_b])*(cos(DEC*pi/180.0)))**2.0 + (DEC - cat_DEC[c_b])**2.0)**0.5
        index = argmin(sep)
        sep_list +=[sep[index]]
        RA_sep += [cat_RA[c_b][index] - RA]
        DEC_sep += [cat_DEC[c_b][index] - DEC]
        xs += [my_X[i]]
        ys += [my_Y[i]]
        x_sep += [RA_sep[-1]*plate_scale*cos(DEC*pi/180.0)]
        y_sep += [DEC_sep[-1]*plate_scale]

    clever = array([x for x in sort(sep_list)])
    
    course_fit = median(clever)

    if course_fit > 3:
        return xs,ys,RA_sep,DEC_sep, array(course_fit)
    
    for i in range(0,len(my_RA)):
        RA = my_RA[i]
        DEC = my_DEC[i]
        sep = 3600*(((RA - cat_RA)*(cos(DEC*pi/180.0)))**2.0 + (DEC - cat_DEC)**2.0)**0.5
        index = argmin(sep)
        sep_list +=[sep[index]]
        RA_sep += [cat_RA[index] - RA]
        DEC_sep += [cat_DEC[index] - DEC]
        xs += [my_X[i]]
        ys += [my_Y[i]]

    sep_list = array(sep_list)
    RA_sep = array(RA_sep)
    DEC_sep = array(DEC_sep)
    xs = array(xs)
    ys = array(ys)

    c = [sep_list < 3*5.0]

    return xs[c],ys[c],RA_sep[c],DEC_sep[c], sep_list[c]
