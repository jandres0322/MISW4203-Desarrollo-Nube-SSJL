from celery import shared_task
from models import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import importlib
import subprocess
import os

@shared_task(name='sync_sqs_logs', bind=True, max_retries=2)
def sync_sqs_logs(self):
    # Lazy import the celery_app object
    celery_app = importlib.import_module('workers.celery').celery_app

    try:
        engine = create_engine(os.environ.get('DATABASE_URL', 'postgresql+psycopg2://root:password@database:5432/convert_tool_video'))

        # Crea el constructor de sesiones
        Session = sessionmaker(bind=engine)

        # Crea una sesión
        session = Session()

        # Realiza la consulta
        tasks = session.query(Task).filter(Task.status == 'Uploaded').all()

        # Imprime los resultados
        self.async_app = celery_app
        for task in tasks:
            self.async_app.send_task("upload_task", args=[task.id, task.path_file, task.new_format])
            print(task.id, task.status)
            new_path = f'{task.path_file.split(".")[0]}.{task.new_format}'
            session.query(Task).filter_by(id=task.id).update(dict(status="Processed",path_file_new_format=new_path))
            session.commit()
        session.close()

    except Exception as e:
        raise self.retry(exc=e)

@shared_task(name="upload_task")
def upload_task(id, path_file, new_format):
    path_batch = os.environ.get('BATCH_URL','batch/convert_video.sh')
    new_path =  f'{path_file.split(".")[0]}.{(new_format.lower())}'
    os.system(f'sh {path_batch} {path_file} {new_path}')
    return id