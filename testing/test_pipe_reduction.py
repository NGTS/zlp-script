import pytest
import numpy as np
from astropy.io import fits
import os
import shutil
import subprocess as sp


root_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))


def render_data(filename, value):
    data = np.ones((2048, 2048)) * value
    phdu = fits.PrimaryHDU(data)
    phdu.writeto(filename)


@pytest.fixture
def master_dark(tmpdir):
    fname = str(tmpdir.join('mdark.fits'))
    render_data(fname, 0.)
    return fname


@pytest.fixture
def master_bias(tmpdir):
    fname = str(tmpdir.join('mbias.fits'))
    render_data(fname, 0.)
    return fname


@pytest.fixture
def master_flat(tmpdir):
    fname = str(tmpdir.join('mflat.fits'))
    render_data(fname, 1.)
    return fname


@pytest.fixture
def image(tmpdir):
    fname = 'IMAGE80220150320023345.fits.bz2'
    dest = str(tmpdir.join(fname))
    src = os.path.join(root_dir, 'testing', 'data', 'action101885_observeField', fname)
    shutil.copyfile(src, dest)
    return dest


@pytest.fixture
def reduce_file(master_bias, master_dark, master_flat, image, tmpdir):
    inlist = tmpdir.join('images.txt')
    inlist.write(os.path.realpath(image))
    biasname = 'mbias.fits'
    darkname = 'mdark.fits'
    flatname = 'mflat.fits'
    caldir = str(tmpdir)
    outdir = caldir

    cmd = ['python', os.path.join(root_dir, 'scripts', 'pipered.py'),
            str(inlist), biasname, darkname, '', flatname, caldir, outdir]
    sp.check_call(cmd)
    return str(tmpdir.join('procIMAGE80220150320023345.fits'))


def test_pipeline_reduction_creates_file(reduce_file):
    assert os.path.isfile(reduce_file)


def test_pipeline_reduction_prints_header_cards(reduce_file):
    with fits.open(reduce_file) as infile:
        history = str(infile[0].header['history'])

    for phrase in ['Overscan of', 'Bias subtracted', 'Dark subtracted',
            'Flat corrected']:
        assert phrase in history
