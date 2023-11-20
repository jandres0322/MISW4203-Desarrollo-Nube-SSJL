#!/bin/bash
echo "Entrando al batch"
path_file=$1
new_path_file=$2
gsutil cp gs://bucketfileserver/$path_file $path_file
ffmpeg -i $path_file -c:v libx264 -c:a aac $new_path_file -y
gsutil cp $new_path_file gs://bucketfileserver/$new_path_file -y
rm $path_file
echo "Proceso completado"