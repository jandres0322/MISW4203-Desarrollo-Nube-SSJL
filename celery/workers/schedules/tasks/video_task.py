from celery import shared_task
from models import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import importlib
import subprocess
import os
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

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

        # Realiza la consulta
        tasks = session.query(Task).filter(Task.status == 'Uploaded').all()

        # Imprime los resultados
        self.async_app = celery_app
        for task in tasks:
            self.async_app.send_task("upload_task", args=[task.path_file, task.new_format])
            print(task.id, task.status)
            new_path = f'{task.path_file.split(".")[0]}.{task.new_format}'
            session.query(Task).filter_by(id=task.id).update(
                dict(status="Processed", path_file_new_format=new_path))
            session.commit()
        session.close()

    except Exception as e:
        raise self.retry(exc=e)


@shared_task(name="upload_task")
def upload_task(path_file, new_format):
    blob = client.get_bucket(bucket_name).blob(path_file)
    local_filename = f'/tmp/{path_file}'
    blob.download_to_filename(local_filename)
    new_path = f'{path_file.split(".")[0]}.{new_format.lower()}'
    subprocess.run(['ffmpeg', '-i', local_filename, '-c:v', 'libx264', '-c:a', 'aac', new_path])
    new_blob = client.get_bucket(bucket_name).blob(new_path)
    new_blob.upload_from_filename(new_path)

    os.remove(local_filename)
