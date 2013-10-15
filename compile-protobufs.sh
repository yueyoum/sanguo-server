#!/bin/bash

protoc --python_out=msg -Iprotobuf protobuf/*.proto

exit $?

