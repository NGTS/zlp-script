# -*- coding: utf-8 -*-

import pytest
import os
import shutil
import subprocess as sp

root_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
script_path = os.path.join(root_dir, 'scripts', 'createlists.py')
assert os.path.isfile(script_path)


@pytest.fixture(scope='module')
def data_dir():
    return os.path.join(root_dir, 'testing', 'data')


def test_build_lists(data_dir, tmpdir):
    run_name = 'create_lists_test'
    cmd = ['python', script_path, os.path.join(data_dir, '*'), 'IMAGE', 'bz2',
           run_name]
    os.chdir(str(tmpdir))
    os.makedirs('output')

    # Run the script
    sp.check_call(cmd)

    # Verify the output files contain only one entry
    for list_name_ending in ['bias', 'dark', 'flat', 'image_NG0953-4538']:
        list_path = '{run_name}_{ending}.list'.format(run_name=run_name,
                                                      ending=list_name_ending)

        with open(os.path.join('output', list_path)) as infile:
            contents = infile.readlines()

        files = [line.strip() for line in contents]
        assert len(files) == 1
