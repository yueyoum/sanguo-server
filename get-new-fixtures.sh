#!/bin/bash

if [ -z "$1" ]
then
    FIXTURES=*
else
    FIXTURES="$1"
fi

scp muzhi@192.168.1.100:/opt/sanguo/editor/fixtures/"$FIXTURES" sanguo/preset/fixtures/
python sanguo/preset/process_fixtures.py

