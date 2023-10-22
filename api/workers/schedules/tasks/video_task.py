from celery import shared_task
from models import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import importlib

@shared_task(name='sync_sqs_logs', bind=True, max_retries=2)
def sync_sqs_logs(self):
    # Lazy import the celery_app object
    celery_app = importlib.import_module('workers.celery').celery_app

    try:
        engine = create_engine('postgresql://root:password@database:5432/convert_tool_video')

        # Crea el constructor de sesiones
        Session = sessionmaker(bind=engine)

        # Crea una sesión   
        session = Session()
    
        # Realiza la consulta
        tasks = session.query(Task).filter(Task.status == 'Uploaded').all()

        # Imprime los resultados
        self.async_app = celery_app
        for task in tasks:
            self.async_app.send_task("upload_task", args=[task.id])
            print(task.id, task.status)

        # Cierra la sesión
        session.close()

    except Exception as e:
        raise self.retry(exc=e)

@shared_task(name="upload_task")
def upload_task(task_id):
    # Actualizar a la base de datos
    print(task_id)
    task= task_id
    return task