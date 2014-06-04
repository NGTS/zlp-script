#!/usr/bin/env bash

run_tests() {
    export PATH=testing/bin:${PATH}
    py.test $*
}

run_tests $*
