#!/bin/bash

protoc --python_out=msg -Iprotobuf protobuf/*.proto

python message-type.py

exit $?

