#!/bin/bash

PWD=`pwd`
cd src

while true
do
  ../venv/bin/python 01_new_data_acquire.py
  ../venv/bin/python 02_ml.py
  sleep 60
done

cd $PWD
