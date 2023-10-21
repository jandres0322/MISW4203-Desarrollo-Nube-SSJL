FROM python:3.8
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN pip install psycopg2
EXPOSE 5000
CMD ["python", "app.py"]