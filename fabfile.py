from fabric.api import *
import os
import socket

def lrun(*args, **kwargs):
    func = local if socket.gethostname() == 'ngtshead'  else run
    return func(*args, **kwargs)

def change_dir(*args, **kwargs):
    func = lcd if socket.gethostname() == 'ngtshead' else cd
    return func(*args, **kwargs)

env.use_ssh_config = True
env.hosts = ['ngtshead']

PIPELINE_DIR = '/ngts/pipedev/ZLP'
change_to_pipeline_dir = lambda: change_dir(PIPELINE_DIR)


@task
def update():
    '''
    Push current changes and update on ngtshead
    '''
    push_local()
    update_remote()


@task
def push_local(remote='origin', branch='master'):
    '''
    Push <remote>/<branch> to remote
    '''
    local('git push {remote} {branch}'.format(remote=remote, branch=branch))


@task
def update_remote(remote='origin', branch='master'):
    '''
    Checkout <remote>/<branch> on ngtshead and update submodules
    '''
    with change_to_pipeline_dir():
        lrun('git fetch {remote}'.format(remote=remote))
        lrun('git checkout {branch}'.format(branch=branch))
        lrun('git merge --ff {remote}/{branch}'.format(remote=remote, branch=branch))
        lrun('git submodule update')
        # Update each submodule completely
        lrun('git submodule foreach git submodule update --init --recursive')


@task
def test_remote(sourcedir='source20150817'):
    '''
    Run test on ngtshead with <sourcedir>
    '''
    update()
    with change_to_pipeline_dir():
        lrun('./test.sh {sourcedir}'.format(sourcedir=sourcedir))


def submodules(fname):
    root_dir = os.path.realpath(os.path.dirname(fname))
    with open(fname) as infile:
        for line in infile:
            if 'path' in line:
                stub = line.strip().split('=')[-1].strip()
                yield os.path.join(root_dir, stub)


@task
def update_submodules():
    '''
    Update all submodules to origin/master
    '''
    for path in submodules('.gitmodules'):
        with lcd(path):
            local('git fetch origin')
            local('git checkout origin/master')


@task
def install_python_packages():
    '''
    Install the required python packages.
    '''
    has_conda = local('conda 2>/dev/null >/dev/null').return_code == 0
    if has_conda:
        local('conda install --file requirements.conda.txt')
    local('pip install -r requirements.txt')


@task
def init():
    '''
    Initialises the pipeline repository
    '''
    install_python_packages()
    local('git submodule init')
    local('git submodule update')
