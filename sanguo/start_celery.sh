#!/bin/bash
SELF=$(readlink -f $0)
PROJECT_PATH=$(dirname $(dirname $SELF))
cd $PROJECT_PATH

source activate_env
cd sanguo

celery worker --app=worker -l info

