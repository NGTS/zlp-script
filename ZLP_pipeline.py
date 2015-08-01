#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import argparse
import subprocess as sp
import os
import shutil
import sys
from contextlib import contextmanager
from socket import gethostname
import re


def abspath(path):
    return os.path.realpath(path)


@contextmanager
def change_dir(path):
    old_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_cwd)


BASE_DIR = abspath(os.path.join(os.path.dirname(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
PIPELINE_BIN = os.path.join('/', 'usr', 'local', 'pipeline')


def setup_directory_structure(root_dir):
    dirs = ['OriginalData/output', 'AperturePhot', 'Reduction',
            'Reduction/output']
    for dirname in dirs:
        path = os.path.join(root_dir, dirname)
        try:
            os.makedirs(path)
        except OSError:
            # Directory must exist
            pass


def run(command):
    str_cmd = list(map(str, command))
    print(' '.join(str_cmd))
    sp.check_call(str_cmd)


def setup_environment():
    # Configure pythonpath
    os.environ['PYTHONPATH'] = ':'.join([
        os.environ.get('PYTHONPATH', ''),
        os.path.join(BASE_DIR, 'scripts', 'zlp-photometry'),
        os.path.join(BASE_DIR, 'scripts'),
        os.path.join(BASE_DIR, 'scripts', 'zlp-input-catalogue')
    ])
    os.environ['PATH'] = ':'.join([os.environ['PATH'], PIPELINE_BIN])

    hostname = gethostname()
    if re.match(r'ngts.*', hostname):
        iers_data = os.path.join(PIPELINE_BIN, '..', 'data')
    elif re.match(r'mbp.*', hostname):
        iers_data = os.path.expanduser(os.path.join('~', '.local', 'data'))

    os.environ['IERS_DATA'] = iers_data
    os.environ['JPLEPH_DATA'] = os.path.join(iers_data,
                                             'linux_p1550p2650.430t')

    os.environ['LD_LIBRARY_PATH'] = ':'.join([
        os.environ.get('LD_LIBRARY_PATH', ''),
        '/opt/intel/composer_xe_2013_sp1.0.080/compiler/lib/intel64'
    ])


def create_input_lists(args, image_key='IMAGE', extension='bz2'):
    script_name = os.path.join(SCRIPTS_DIR, 'createlists.py')

    image_dirs = os.path.join(args.root_directory, 'OriginalData', 'images',
                              '**', '*')
    run_name = args.run_name

    cmd = ['python', script_name, image_dirs, image_key, extension, run_name]
    run(cmd)


def create_master_bias(args):
    bias_list = os.path.join(args.root_directory, 'OriginalData', 'output',
                             '{run_name}_bias.list'.format(
                                 run_name=args.run_name))

    bias_stub = '{run_name}_MasterBias.fits'.format(run_name=args.run_name)
    output_dir = os.path.join(args.root_directory, 'Reduction', 'output',
                              args.run_name)

    script_name = os.path.join(SCRIPTS_DIR, 'zlp-reduction', 'bin',
                               'pipebias.py')
    cmd = ['python', script_name, bias_list, bias_stub, output_dir]
    run(cmd)
    return bias_stub


def create_master_dark(bias_stub, args):
    dark_list = os.path.join(args.root_directory, 'OriginalData', 'output',
                             '{run_name}_dark.list'.format(
                                 run_name=args.run_name))

    dark_stub = '{run_name}_MasterDark.fits'.format(run_name=args.run_name)
    output_dir = os.path.join(args.root_directory, 'Reduction', 'output',
                              args.run_name)

    script_name = os.path.join(SCRIPTS_DIR, 'zlp-reduction', 'bin',
                               'pipedark.py')
    cmd = ['python', script_name, dark_list, bias_stub, dark_stub, output_dir]
    run(cmd)
    return dark_stub


def create_master_flat(dark_stub, bias_stub, shuttermap_path, args):
    flat_list = os.path.join(args.root_directory, 'OriginalData', 'output',
                             '{run_name}_flat.list'.format(
                                 run_name=args.run_name))

    flat_stub = '{run_name}_MasterFlat.fits'.format(run_name=args.run_name)
    output_dir = os.path.join(args.root_directory, 'Reduction', 'output',
                              args.run_name)

    script_name = os.path.join(SCRIPTS_DIR, 'zlp-reduction', 'bin',
                               'pipeflat.py')
    cmd = ['python', script_name, flat_list, bias_stub, dark_stub,
           shuttermap_path, flat_stub, output_dir]
    run(cmd)
    return flat_stub


def copy_temporary_shuttermap(args):
    dest = os.path.join(args.root_directory, 'Reduction', 'output',
                        args.run_name, os.path.basename(args.shuttermap))
    shutil.copyfile(args.shuttermap, dest)
    return dest


def main(args):
    setup_environment()
    setup_directory_structure(args.root_directory)

    #     with change_dir(os.path.join(args.root_directory, 'OriginalData')):
    #         create_input_lists(args)

    with change_dir(os.path.join(args.root_directory, 'Reduction')):
        bias_name = create_master_bias(args)
        dark_name = create_master_dark(bias_name, args)
        shuttermap_path = copy_temporary_shuttermap(args)
        flat_name = create_master_flat(dark_name, bias_name, shuttermap_path,
                                       args)

    print('Pipeline finished')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--run-name', required=True)
    parser.add_argument('-d', '--root-directory', required=True)
    parser.add_argument('-i', '--input-catalogue', required=True)
    parser.add_argument('-w', '--initial-wcs-solution', required=True)
    parser.add_argument('-c', '--confidence-map', required=True)
    parser.add_argument('-s', '--shuttermap', required=True)
    parser.add_argument('-R', '--wcs-reference-frame', required=True)
    main(parser.parse_args())

    # Exit with failure to prevent verification
    sys.exit(1)
