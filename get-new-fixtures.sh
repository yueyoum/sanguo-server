#!/bin/bash

scp muzhi@192.168.1.100:/opt/sanguo/editor/fixtures/* sanguo/preset/fixtures/
python sanguo/preset/process_fixtures.py

