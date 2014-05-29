#!/bin/bash
SELF=$(readlink -f $0)
PROJECT_PATH=$(dirname $(dirname $(dirname $SELF)))
cd $PROJECT_PATH

source activate_env
cd sanguo

python cron/reset_counter.py
python cron/reset_checkin.py
python cron/reset_stage_elite.py
python cron/reset_task.py
python cron/reset_store_player_limit.py

exit 0

