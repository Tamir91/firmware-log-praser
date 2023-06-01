#!/bin/bash
log=$(cat $1 | tr ',' '\n')
i=0
j=0
echo -n "FW_Log_Data:"
for l in $log; do
    j=$((j+1))
    if [ $j -le 4 ]; then
        continue
    fi
    i=$((i+1))
    printf "%02X " $l
    if [ $((i % 20)) -eq 0 ]; then
        echo
        # echo -n "$(date '+%Y-%m-%d %H:%M:%S')  FW_Log_Data:"
        echo -n "FW_Log_Data:"
    fi
done