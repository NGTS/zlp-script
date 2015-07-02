from fabric.api import *
import os

env.use_ssh_config = True
env.hosts = ['ngtshead.astro']

PIPELINE_DIR = '~/work/NGTS/pipeline/ZLP/zlp-script'
change_to_pipeline_dir = lambda: cd(PIPELINE_DIR)


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
        run('git fetch {remote}'.format(remote=remote))
        run('git checkout {branch}'.format(branch=branch))
        run('git merge --ff {remote}/{branch}'.format(remote=remote, branch=branch))
        run('git submodule update')


@task
def test_remote(sourcedir='source2015'):
    '''
    Run test on ngtshead with <sourcedir>
    '''
    with change_to_pipeline_dir():
        run('./test.sh {sourcedir}'.format(sourcedir=sourcedir))


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
