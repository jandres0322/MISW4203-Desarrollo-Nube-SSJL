#!/bin/bash

$cadena=$1

subcadenas=$(split -a 1 "$cadena" "/")

path_file=${subcadenas[0]}
path_new_file=${subcadenas[1]}

ffmpeg -i "$path_file" -o "$path_new_file"