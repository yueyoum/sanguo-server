#!/bin/bash

dump() {
    declare -a arr
    arr=(`echo "$1" | tr ':', ' '`)
    echo ${arr[@]}
    python manage.py dumpdata ${arr[0]} --indent=4 > preset/fixtures/${arr[1]}
}


while read LINE
do
    dump "$LINE"
done < datatable

exit 0
