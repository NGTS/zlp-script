from fabric.api import *

env.use_ssh_config = True
env.hosts = ['ngtshead.astro']

PIPELINE_DIR = '~/work/NGTS/pipeline/ZLP/zlp-script'
change_to_pipeline_dir = lambda: cd(PIPELINE_DIR)


@task(default=True)
def update():
    push_local()
    update_remote()


@task
def push_local(remote='origin', branch='master'):
    local('git push {remote} {branch}'.format(remote=remote, branch=branch))


@task
def update_remote(remote='origin', branch='master'):
    with change_to_pipeline_dir():
        run('git fetch {remote}'.format(remote=remote))
        run('git checkout {branch}'.format(branch=branch))
        run('git merge --ff {remote}/{branch}'.format(remote=remote, branch=branch))
        run('git submodule update')

@task
def test_remote(sourcedir='source2015'):
    with change_to_pipeline_dir():
        run('./test.sh {sourcedir}'.format(sourcedir=sourcedir))
