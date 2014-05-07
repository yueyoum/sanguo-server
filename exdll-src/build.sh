#!/bin/bash

swig -c++ -python external_calculate.i
g++ -o _external_calculate.so -fPIC -shared external_calculate.cpp external_calculate_wrap.cxx -I /usr/include/python2.7

