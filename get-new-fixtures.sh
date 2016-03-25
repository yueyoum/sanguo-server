#!/bin/bash

if [ -z "$1" ]
then
    echo "no platform. wp or ios2"
    exit
fi



if [[ $1 == "wp" ]]
then
    scp muzhi@work.mztimes.com:/opt/sanguo/editor/fixtures/* sanguo/preset/fixtures/
elif [[ $1 == "ios2" ]]
then
    scp muzhi@work.mztimes.com:/opt/sanguo/editor_ios2/fixtures/* sanguo/preset/fixtures/
else
    echo "wrong platform."
    exit
fi

python sanguo/preset/process_fixtures.py

