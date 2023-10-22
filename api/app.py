from flask import Flask, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Task, db
from functools import wraps
import jwt
import datetime
import os


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

app.config['JWT_TIME_EXPIRE'] = int(os.environ.get('JWT_TIME_EXPIRE',1200))
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY", "JF}]&p1CH4-?-k]")

app_context = app.app_context()
app_context.push()

db.init_app(app)
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
    valid_formats = ["MP4", "WEBM", "AVI", "MPEG", "WMV"]
    data = request.get_json()
    file_name = data.get('fileName')
    previous_format = file_name.split(".")[1]
    new_format = data.get('newFormat').upper()
    task = Task.query.filter_by(file_name = file_name).first()
    
    if task:
        return make_response(
            jsonify({
                'message': 'Ya existe una tarea para este archivo {}'.format(new_format)
            }),
            400
        )
    
    if not previous_format in valid_formats:
        return make_response(
            jsonify({
                'message': 'El formato de origen es inválido.'
            }),
            400    
        )       

    if not new_format in valid_formats:
        return make_response(
            jsonify({
                'message': 'El nuevo formato es inválido.'
            }),
            400    
        )
    task = Task(
        file_name = file_name,
        new_format = new_format,
        user = user
    )
    db.session.add(task)
    db.session.commit()
    return make_response(
        jsonify({
            'message': 'Tarea creada exitosamente!',
        })
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