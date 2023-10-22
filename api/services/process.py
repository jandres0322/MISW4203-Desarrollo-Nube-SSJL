import json
from api.models import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def read_messages_queue(self):
    # Crea el motor de base de datos
    engine = create_engine('postgresql://root:password@localhost:5432/convert_tool_video')

    # Crea el constructor de sesiones
    Session = sessionmaker(bind=engine)

    # Crea una sesión   
    session = Session()
    # Realiza la consulta
    
    # Realiza la consulta
    tasks = session.query(Task).filter(Task.status == 'Uploaded').all()

    # Imprime los resultados
    for task in tasks:
      print(task.id, task.status)

    # Cierra la sesión
    session.close()
    print('Testing')
