#!/bin/bash

PWD=`pwd`
cd src

../venv/bin/python 01_new_data_acquire.py
../venv/bin/python 02_ml.py

cd $PWD
