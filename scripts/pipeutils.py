from contextlib import contextmanager
import bz2
from astropy.io import fits


@contextmanager
def open_fits_file(filename):
    if filename.endswith('.bz2'):
        with bz2.BZ2File(filename) as uncompressed:
            with fits.open(uncompressed) as infile:
                yield infile
    else:
        with fits.open(filename) as infile:
            yield infile
