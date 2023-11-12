from flask import Flask, request, jsonify, make_response, url_for, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import User, Task, db
from functools import wraps
import jwt
import datetime
import os
from flask_migrate import Migrate
from utils import allowed_file, create_user_folder
from sqlalchemy import desc, asc, delete
from dotenv import load_dotenv

load_dotenv()

VOLUME_PATH = os.environ.get('UPLOAD_URL')
app = Flask(__name__)
migrate = Migrate()

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_ENGINE') + '://' + \
    os.environ.get('DB_USER') + ':' + \
    os.environ.get('DB_PASSWORD') + '@' + \
    os.environ.get('DB_HOST') + ':' + \
    os.environ.get('DB_PORT') + '/' + \
    os.environ.get('DB_NAME')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_TIME_EXPIRE'] = int(os.environ.get('JWT_TIME_EXPIRE'))
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')

app_context = app.app_context()
root_path = app.root_path
app_context.push()

db.init_app(app)
migrate.init_app(app, db)
db.create_all()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'authorization' in request.headers:
            token = request.headers['authorization']
            token = token.split(" ")[1]
        if not token:
            return jsonify({'message': 'El token no encontrado'}), 401
        print(token)
        try:
            data = jwt.decode(
                token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query\
                .filter_by(username=data['username'])\
                .first()
        except Exception as e:
            print(e)
            return jsonify({
                'message': 'El token es invalido'
            }), 401
        return f(current_user, *args, **kwargs)

    return decorated


@app.route('/api/auth/login', methods=['POST'])
def login_user():
    auth = request.get_json()
    if not auth or not auth.get('username') or not auth.get('password'):
        return make_response(
            jsonify({
                'message': 'No hay información correspondiente'
            }),
            401
        )
    user = User.query.filter_by(username=auth.get('username')).first()
    if not user:
        return make_response(
            jsonify({
                'messaage': 'El usuario {} no se encuentra registrado'.format(auth.get('username')),
            }),
            401
        )
    if not check_password_hash(user.password, auth.get('password')):
        return make_response(
            jsonify({
                'message': 'La contraseña no coincide',
            }),
            401
        )
    payload = {
        'username': auth.get('username'),
        'password': auth.get('password'),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=app.config['JWT_TIME_EXPIRE'])
    }
    token = jwt.encode(
        payload, app.config['JWT_SECRET_KEY'], algorithm="HS256")
    return make_response(
        jsonify({
            "token": token
        }),
        200
    )


@app.route('/api/auth/signup', methods=['POST'])
def register_user():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password1 = data.get('password1')
    password2 = data.get('password2')
    if password1 != password2:
        return make_response(
            jsonify({
                'message': 'Las contraseñas no coinciden'
            }),
            400
        )
    user = User.query.filter_by(email=email).first()
    if user:
        return make_response(
            jsonify({
                'messsage': 'Ya existe un usuario con el correo {}'.format(email)
            }),
            400
        )
    user = User(
        username=username,
        password=generate_password_hash(password1),
        email=email
    )
    db.session.add(user)
    db.session.commit()
    return make_response(
        jsonify({
            'message': 'Usuario creado exitosamente!',
        }),
        201
    )


@app.route('/api/tasks', methods=['POST'])
@token_required
def create_task(user):
    new_format = request.form['new_format']
    file = request.files['file']
    if 'file' not in request.files:
        make_response(
            jsonify({
                'message': 'No se carga el archivo'
            }), 404
        )
    if file and allowed_file(file.filename):
        make_response(
            jsonify({
                'message': 'El archivo no tiene un formato valido'
            }), 400
        )
    filename_secure = secure_filename(file.filename)
    folder_user = create_user_folder(VOLUME_PATH, user.username)
    filename_path = os.path.join(folder_user, filename_secure)
    task = Task.query.filter_by(path_file=filename_path).first()
    if task:
        return make_response(
            jsonify({
                'message': 'Ya existe una tarea para este archivo'
            }),
            400
        )
    file.save(filename_path)
    task = Task(
        path_file=filename_path,
        new_format=new_format.lower(),
        user_id=user.id
    )
    db.session.add(task)
    db.session.commit()
    return make_response(
        jsonify({
            'message': 'Tarea creada correctamente!'
        }), 201
    )


@app.route('/api/tasks', methods=['GET'])
@token_required
def get_user_tasks(user):
    max_tasks = request.args.get('max')
    order = request.args.get('order')
    tasks = Task.query \
                .filter_by(user_id=user.id) \
                .order_by(asc(Task.id) if order == '0' else desc(Task.id))
    if max_tasks:
        tasks = tasks.limit(max_tasks).all()
    tasks_list = [
        {
            'id': task.id,
            'path_file': task.path_file,
            'path_file_new_format': task.path_file_new_format,
            'original_extension': task.path_file.split('.')[-1],
            'new_format': task.new_format,
            'available': task.status == 'Processed'
        } for task in tasks
    ]
    return make_response(
        jsonify({
            "length": len(tasks_list),
            "tasks": tasks_list
        }), 200
    )


@app.route('/api/task/<int:task_id>', methods=['GET'])
@token_required
def get_task_by_id(user, task_id):
    task = Task.query.filter_by(id=task_id).first()
    if not task:
        return make_response(jsonify({'message': 'Tarea no encontrada'}), 404)
    return make_response(
        jsonify({
            'url_original_file': task.path_file,
            'url_processed_file': task.path_file_new_format,
            'status': task.status,
            'new_format': task.new_format,
        }), 200
    )


@app.route('/api/tasks/upload', methods=['GET'])
@token_required
def download_file(user):
    path_file_upload = request.args.get('path')
    path, filename = os.path.split(path_file_upload)
    return send_from_directory(path, filename)


@app.route('/api/task/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(user, task_id):
    task = Task.query.filter_by(id=task_id).first()
    if not task:
        return make_response(jsonify({'message': 'Tarea no encontrada'}), 404)
    path_file = task.path_file
    path_new_file = task.path_file_new_format
    os.system(f'rm -rf {path_file}')
    if path_new_file is not None:
        os.system(f'rm -rf {path_new_file}')
    db.session.delete(task)
    db.session.commit()
    return make_response(
        jsonify({
            'message': 'Tarea eliminada correctamente!'
        }), 200
    )


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT'))
    )
