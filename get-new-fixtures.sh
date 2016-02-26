#!/bin/bash

if [ -z "$1" ]
then
    FIXTURES=*
else
    FIXTURES="$1"
fi

scp muzhi@work.mztimes.com:/opt/sanguo/editor/fixtures/"$FIXTURES" sanguo/preset/fixtures/
python sanguo/preset/process_fixtures.py

