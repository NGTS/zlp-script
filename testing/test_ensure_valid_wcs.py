import fitsio
from ngts_catalogue.wcs_fitting import ensure_valid_wcs
import numpy as np

def test_ensure_valid_wcs(tmpdir):
    out_filename = tmpdir.join('data.fits')
    with fitsio.FITS(str(out_filename), 'rw') as fits:
        header_keys = ['CTYPE1', 'CTYPE2', 'CRVAL1', 'CRVAL2', 'CRPIX1', 'CRPIX2', 'CD1_1',
        'CD2_2', 'CD1_2', 'CD2_1', 'PV2_1', 'PV2_3', 'PV2_5']
        header_values = [ 'RA---TAN', 'DEC--TAN', 285.882518822083, 49.1645834443476,
                996.850742526356, 1039.41668305912, 0.00138591466083086, 0.0013859166370424,
                1.39376792562736E-05, -1.40028141086235E-05, 0.999993897433, 8.112927254280001,
                901.974288037, ]


        data = np.arange(2*3, dtype='i4').reshape(2, 3)
        header = [ {'name': key, 'value': value, 'comment': 'Comment' }
                            for (key, value) in zip(header_keys, header_values)]

        fits.write(data, header=header)

    target = { key: value for (key, value) in zip(header_keys, header_values)
            if key not in ('CTYPE1', 'CTYPE2')}
    target['CTYPE1'] = 'RA---ZPN'
    target['CTYPE2'] = 'DEC--ZPN'

    ensure_valid_wcs(str(out_filename))


    with fitsio.FITS(str(out_filename)) as fits:
        header = fits[0].read_header()
        for key, value in target.iteritems():
            assert header[key] == value

