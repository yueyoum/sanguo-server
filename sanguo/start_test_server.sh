#!/bin/bash

export PYTHONPATH=$PYTHONPATH:../

python manage.py runserver 0.0.0.0:8000 --settings=sanguo.test_settings

