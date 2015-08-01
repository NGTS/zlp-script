#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import subprocess as sp
import os
import shutil
import sys


def abspath(path):
    return os.path.realpath(path)


def main(args):
    print(args)


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
