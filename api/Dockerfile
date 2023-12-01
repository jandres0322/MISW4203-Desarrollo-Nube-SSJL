FROM python:3.10
WORKDIR /src/app
COPY . .
RUN pip install -r requirements.txt
RUN apt-get -y update
RUN apt-get install ffmpeg libsm6 libxext6  -y
EXPOSE 5000
CMD ["python", "app.py"]