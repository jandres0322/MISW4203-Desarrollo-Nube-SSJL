from celery import shared_task
from models import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@shared_task(name='sync_sqs_logs', bind=True, max_retries=2)
def sync_sqs_logs(self):
    
    try:
        engine = create_engine('postgresql://root:password@database:5432/convert_tool_video')

        # Crea el constructor de sesiones
        Session = sessionmaker(bind=engine)

        # Crea una sesión   
        session = Session()
    
        # Realiza la consulta
        tasks = session.query(Task).filter(Task.status == 'Uploaded').all()

        # Imprime los resultados
        for task in tasks:
            print(task.id, task.status)

        # Cierra la sesión
        session.close()

    except Exception as e:
        raise self.retry(exc=e)
