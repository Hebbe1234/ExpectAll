#!/bin/bash

arr=()

arr+=(1)
arr+=(2)

str="$(IFS=:; echo "${arr[*]}")"

echo $str