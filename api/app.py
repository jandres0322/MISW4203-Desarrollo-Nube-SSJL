from flask import Flask, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import User, Task, db
from functools import wraps
import jwt
import datetime
import os
from flask_migrate import Migrate
from utils import allowed_file, create_user_folder

UPLOAD_FOLDER = "uploads/videos"
app = Flask(__name__)
migrate = Migrate()

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "postgresql+psycopg2://test:test@localhost:5432/convert_tool_video")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  
app.config['JWT_TIME_EXPIRE'] = int(os.environ.get('JWT_TIME_EXPIRE',1200))
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY", "JF}]&p1CH4-?-k]")

app_context = app.app_context()
app_context.push()

db.init_app(app)
migrate.init_app(app,db)
db.create_all()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'authorization' in request.headers:
            token = request.headers['authorization']
            token = token.split(" ")[1]
        if not token:
            return jsonify({'message' : 'El token no encontrado'}), 401
        print(token)
        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms = ["HS256"])
            current_user = User.query\
                .filter_by(username = data['username'])\
                .first()
        except Exception as e:
            print(e)
            return jsonify({
                'message' : 'El token es invalido'
            }), 401
        return  f(current_user, *args, **kwargs)
  
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
    user = User.query.filter_by(username = auth.get('username')).first()
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
    token = jwt.encode(payload, app.config['JWT_SECRET_KEY'],algorithm="HS256")
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
    user = User.query.filter_by(email = email).first()
    if user:
        return make_response(
            jsonify({
                'messsage': 'Ya existe un usuario con el correo {}'.format(email)
            }),
            400
        )
    user = User(
        username = username,
        password = generate_password_hash(password1),
        email = email
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
    folder_user  = create_user_folder( app.config['UPLOAD_FOLDER']  ,user.username)
    filename_path = os.path.join(folder_user, filename_secure) 
    file.save(filename_path)
    task = Task(
        path_file=filename_path,
        new_format=new_format,
        user_id=user.id
    )
    db.session.add(task)
    db.session.commit()
    return make_response(
        jsonify({
            'message': 'Tarea creada correctamente!'
        }), 201
    )

@app.route('/api/users/<int:user_id>/tasks', methods=['GET'])
@token_required
def get_user_tasks(user_id):

    user = User.query.filter_by(id=user_id).first()

    if not user:
        return make_response(jsonify({'message': 'Usuario no encontrado'}), 404)

    user_tasks = Task.query.filter_by(user_id=user.id).all()

    if not user_tasks:
        return make_response(jsonify({'message': 'El usuario no tiene tareas de conversión'}), 404)

    tasks_data = []
    for task in user_tasks:
        task_info = {
            'id': task.id,
            'file_name': task.file_name,
            'original_extension': task.file_name.split('.')[-1],
            'new_format': task.new_format,
            'available': task.status == 'Uploaded'
        }
        tasks_data.append(task_info)

    return make_response(jsonify(tasks_data), 200)

@app.route('/api/task/<int:task_id>', methods=['GET'])
@token_required
def get_task_by_id(usuario, task_id):
    print(task_id)
    print(usuario)
    task = Task.query.filter_by(id=task_id).first()
    if not task:
         return make_response(jsonify({'message': 'Tarea no encontrada'}), 404)
    task_info = {
            'id': task.id,
            'file_name': task.file_name,
            'original_extension': task.file_name.split('.')[-1],
            'new_format': task.new_format,
            'available': task.status == 'Uploaded'
        }
    return make_response(jsonify(task_info), 200)

@app.route('/api/example', methods=['POST'])
@token_required
def protected_route_example(usuario):
    print("==== PROTECTED ROUTE EXAMPLE ==== ")
    return make_response(
        jsonify({
            "message": "Acceso a ruta protegida"
        }),
        200
    )


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )