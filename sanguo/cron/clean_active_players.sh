#!/bin/bash
SELF=$(readlink -f $0)
PROJECT_PATH=$(dirname $(dirname $(dirname $SELF)))
cd $PROJECT_PATH

source activate_env
cd sanguo

python cron/clean_active_players.py

exit 0

