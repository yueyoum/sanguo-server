#!/bin/bash

cd exdll-src
./build.sh

cp external_calculate.py ../sanguo/dll
cp _external_calculate.so ../sanguo/dll

cd ..
exit 0

