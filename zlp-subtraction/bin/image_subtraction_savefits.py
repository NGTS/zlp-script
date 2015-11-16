import pyfits
import glob
import cPickle
import sys
from numpy import *

DEBUG=False

workingdir = sys.argv[1]
starlist   = sys.argv[2]
fitsfile   = sys.argv[3]

hdustars   = pyfits.open(starlist)
stardata   = hdustars[1].data
stars      = len(hdustars[1].data['X_coordinate'])
xs         = hdustars[1].data.field('X_coordinate')
ys         = hdustars[1].data.field('Y_coordinate')
allidents  = []
for i in range(stars):
  x = xs[i]
  y = ys[i]
  allidents.append("%s_%s" % (x,y))

allidents = array(allidents)
 
hdustars.close()
liste = glob.glob('%s/NGTS_IS_*.p' % workingdir)
liste.sort()

frames = len(liste)


allflux      = zeros([stars,frames])
allerrors    = zeros([stars,frames])
allframes    = array(zeros(frames), dtype=[('IMAGEID','S26'), ('JD', 'f8')])

for i,item in enumerate(liste):
  f=open(item ,'rb')
  data = cPickle.load(f)
  f.close()
  idents = data[0]
  idents = array(idents)
  idx = in1d(allidents, idents)
  flc        = data[1]
  elc        = data[2]
  flag       = data[3]
  xs         = data[4]
  ys         = data[5]
  rlc        = data[6]
  imageid    = data[7]
  date       = data[8]
  indices    = data[9]

  flux   = rlc - flc   
  allflux[indices,i]=flux
  allerrors[indices,i]=elc
  allframes[i] = (imageid,date)
  if not DEBUG:
    os.remove(item)

col1 = pyfits.Column(name='IMAGEID', format='26A', array=allframes['IMAGEID'])
col2 = pyfits.Column(name='JD', format='E', array=allframes['JD'])
cols = pyfits.ColDefs([col1, col2])


hdu = pyfits.PrimaryHDU()

tbhdu = pyfits.new_table(cols)

hdu2 = pyfits.ImageHDU(allflux)
hdu3 = pyfits.ImageHDU(allerrors)

hdulist = pyfits.HDUList([hdu,tbhdu,hdu2,hdu3])
hdulist.writeto(fitsfile)
