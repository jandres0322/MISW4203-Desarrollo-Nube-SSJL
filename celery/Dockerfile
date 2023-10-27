FROM python:3.8
WORKDIR /src/app
COPY . .
RUN pip install -r requirements.txt
RUN apt-get -y update
RUN apt-get install ffmpeg libsm6 libxext6  -y
