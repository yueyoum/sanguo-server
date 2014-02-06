#!/bin/bash

cd dll
make sanguo.so
cp sanguo.so ../sanguo/dll
make clean

cd ..

exit 0


