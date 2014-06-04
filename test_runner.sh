#!/usr/bin/env bash

run_tests() {
    export PATH=testing/bin:${PATH}
    py.test -x $*
}

run_tests $*
