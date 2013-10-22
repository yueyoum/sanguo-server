#!/bin/bash

protoc --python_out=protomsg -Iprotobuf protobuf/*.proto

python message-type.py

exit $?

