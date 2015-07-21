#!/usr/bin/env sh

REPONAME=/home/vagrant/ZLP

set -eu

git clone git@github.com:NGTS/zlp-script.git ${REPONAME}

cd ${REPONAME}
git submodule init
git submodule update
git submodule foreach git submodule init
git submodule foreach git submodule update
