#!/bin/bash
echo "Entrando al batch"
path_file=$1
new_path_file=$2
ffmpeg -i $path_file -c:v libx264 -c:a aac $new_path_file