#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import subprocess as sp
import os
import shutil
import sys
import abc
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


class PipelineTask(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, **params):
        self.__dict__.update(**params)

    @abc.abstractmethod
    def command(self):
        pass

    def run(self):
        str_cmd = list(map(str, self.command()))
        print(str_cmd)
        sp.check_call(str_cmd)


class CreateInputLists(PipelineTask):

    def __init__(self, image_dirs, run_name,
                 image_key='IMAGE',
                 extension='bz2'):
        super(CreateInputLists, self).__init__(image_dirs=image_dirs,
                                               run_name=run_name,
                                               image_key=image_key,
                                               extension=extension)
        self.script_name = os.path.join(SCRIPTS_DIR, 'createlists.py')

    @classmethod
    def from_args(cls, args):
        image_dirs = os.path.join(args.root_directory, 'OriginalData',
                                  'images', '**', '*')
        return cls(image_dirs=image_dirs, run_name=args.run_name)

    def command(self):
        return ['python', self.script_name, self.image_dirs, self.image_key,
                self.extension, self.run_name]


def setup_environment():
    # Configure pythonpath
    sys.path.extend([
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


def main(args):
    setup_environment()
    # setup_directory_structure()
    # c = CreateInputLists.from_args(args)
    # with change_dir(os.path.join(args.root_directory, 'OriginalData')):
    #     c.run()

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
