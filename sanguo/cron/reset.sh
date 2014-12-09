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
python cron/reset_prize.py
python cron/set_yueka.py
python cron/reset_friend_plunder_times.py
python cron/clean_union.py

python cron/clean_mail.py
python cron/clean_battle_record.py

exit 0

