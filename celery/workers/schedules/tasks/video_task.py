from celery import shared_task
from models import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import importlib
import subprocess
import os
from dotenv import load_dotenv
from google.cloud import storage
from google.cloud import pubsub_v1
import json

load_dotenv()

subscriber = pubsub_v1.SubscriberClient()

client = storage.Client()
bucket_name = os.environ.get('BUCKET_NAME_STORAGE', 'bucketfileserver' )

@shared_task(name='sync_sqs_logs', bind=True, max_retries=2)
def sync_sqs_logs(self):
    # Lazy import the celery_app object
    celery_app = importlib.import_module('workers.celery').celery_app

    try:
        engine = create_engine(
            os.environ.get('DB_ENGINE') + '://' +
            os.environ.get('DB_USER') + ':' +
            os.environ.get('DB_PASSWORD') + '@' +
            os.environ.get('DB_HOST') + ':' +
            os.environ.get('DB_PORT') + '/' +
            os.environ.get('DB_NAME')
        )

        # Crea el constructor de sesiones
        Session = sessionmaker(bind=engine)

        # Crea una sesión
        session = Session()

        # Realiza la consulta al pub/sub
        subscription_path = subscriber.subscription_path('misw4203-desarrollo-nube-05', 'converter-sub')

        while True:
            response = subscriber.pull(subscription=subscription_path, max_messages = 5)
            print(response)
            received_messages = response.received_messages
            print(received_messages)

            if not received_messages:
                break
            self.async_app = celery_app
            for received_message in received_messages:
                message_data_str = received_message.message.data.decode("utf-8")
                message_data = json.loads(message_data_str)

                id = message_data["id"]
                new_format = message_data["new_format"]
                file_path = message_data["file_path"]
                status = message_data["status"]

                # Imprime los resultados
                self.async_app.send_task("upload_task", args=[id, file_path, new_format])
                print(id, status)
                new_path = f'{file_path.split(".")[0]}.{new_format}'
                session.query(Task).filter_by(id=id, status='Uploaded').update(
                    dict(status="Processed", path_file_new_format=new_path)
                )
                session.commit()

                ack_ids = [received_message.ack_id]
                subscriber.acknowledge(subscription_path, ack_ids)
        session.close()
    except Exception as e:
        raise self.retry(exc=e)


@shared_task(name="upload_task")
def upload_task(id,path_file, new_format):
    blob = client.get_bucket(bucket_name).blob(path_file)
    local_filename = f'/tmp/{path_file}'
    local_folder = f'/tmp/{path_file.split("/")[0]}'
    if not os.path.exists(local_folder):
        print("no existe la carpeta")
        os.makedirs(local_folder)
    blob.download_to_filename(local_filename)
    path_without_extension = path_file.split(".")[0]
    new_path = f'/tmp/{path_without_extension}.{new_format.lower()}'
    subprocess.run(['ffmpeg', '-i', local_filename, '-c:v', 'libx264', '-c:a', 'aac', new_path])
    new_file_bucket = f'{path_without_extension}.{new_format.lower()}'
    new_blob = client.get_bucket(bucket_name).blob(new_file_bucket)
    new_blob.upload_from_filename(new_path)

    os.remove(local_filename)
    return id
