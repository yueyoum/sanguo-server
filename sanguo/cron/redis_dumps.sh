#!/bin/bash
SELF=$(readlink -f $0)
PROJECT_PATH=$(dirname $(dirname $(dirname $SELF)))
cd $PROJECT_PATH

source activate_env
cd sanguo

LOG_FILE=logs/redis_dumps.log

echo -n `date +"%Y-%m-%d %H:%M:%S"` >> $LOG_FILE
echo -n ' ' >> $LOG_FILE
python manage.py redis dumps >> $LOG_FILE

exit 0

