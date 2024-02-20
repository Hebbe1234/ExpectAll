#!/bin/bash

arr=()

arr+=(1)
arr+=(2)

str="$(IFS=:; echo "${arr[*]}")"

echo $str


str1="hi"
str2="there"
str3="$str1$str2"
echo $str3