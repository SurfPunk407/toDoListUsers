from flask import Flask, request, jsonify, session, abort
import os
import logging
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
CORS(app, origins=["http://todolistusers.wuaze.com"])
app.secret_key = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Recommended
#app.config['CORS_HEADERS'] = 'Content-Type'

#db.init_app(app)
db = SQLAlchemy(app)

from models import User, Task

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

with app.app_context():  
    db.create_all()

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            logging.error("Invalid request data for registration")
            return jsonify({'message': 'Invalid request data'}), 400

        username = data['username']
        password = data['password']

        if User.query.filter_by(username=username).first():
            logging.warning(f"Username '{username}' already exists")
            return jsonify({'message': 'Username already exists'}), 400

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        logging.info(f"User '{username}' registered successfully")
        return jsonify({'message': 'User registered successfully'}), 201

    except Exception as e:
        logging.error(f"Error during registration: {e}")
        db.session.rollback() #rollback the transaction in case of an error.
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            logging.error("Invalid request data for login")
            return jsonify({'message': 'Invalid request data'}), 400

        username = data['username']
        password = data['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['username'] = username
            logging.info(f"User '{username}' logged in successfully")
            return jsonify({'message': 'Logged in successfully'}), 200
        else:
            logging.warning(f"Invalid login attempt for user '{username}'")
            return jsonify({'message': 'Invalid username or password'}), 401
    except Exception as e:
        logging.error(f"Error during login: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/logout')
def logout():
    session.pop('username', None)
    logging.info("User logged out")
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'username' not in session:
        logging.warning("Unauthorized access to tasks")
        return jsonify({'message': 'Unauthorized'}), 401

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        logging.error(f"User '{session['username']}' not found in the database")
        return jsonify({'message': 'User not found'}), 404

    try:
        if request.method == 'GET':
            tasks = Task.query.filter_by(user_id=user.id).all()
            logging.info(f"Tasks retrieved for user '{user.username}'")
            return jsonify([task.to_dictionary() for task in tasks])

        elif request.method == 'POST':
            data = request.get_json()
            if not data or 'task' not in data:
                logging.error("Invalid task data")
                return jsonify({'message': 'Invalid task data'}), 400

            new_task = Task(
                task=data['task'],
                description=data.get('description', ''),
                priority=data.get('priority', ''),
                status=data.get('status', True),
                task_date=data.get('task_date', ''),
                user_id=user.id
            )
            db.session.add(new_task)
            db.session.commit()
            logging.info(f"Task created for user '{user.username}'")
            return jsonify(new_task.to_dictionary()), 201

    except Exception as e:
        logging.error(f"Error in tasks route: {e}")
        db.session.rollback()
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/tasks/<int:id>', methods=['PUT', 'DELETE'])
def task(id):
    if 'username' not in session:
        logging.warning("Unauthorized access to task modification")
        return jsonify({'message': 'Unauthorized'}), 401

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        logging.error(f"User '{session['username']}' not found in the database")
        return jsonify({'message': 'User not found'}), 404

    task = Task.query.filter_by(id=id, user_id=user.id).first()
    if not task:
        logging.warning(f"Task with id '{id}' not found for user '{user.username}'")
        return jsonify({'message': 'Task not found'}), 404

    try:
        if request.method == 'PUT':
            data = request.get_json()
            if not data:
                logging.error("Invalid update task data")
                return jsonify({'message': 'Invalid update data'}),400

            task.task = data.get('task', task.task)
            task.description = data.get('description', task.description)
            task.priority = data.get('priority', task.priority)
            task.status = data.get('status', task.status)
            task.task_date = data.get('task_date', task.task_date)
            db.session.commit()
            logging.info(f"Task '{id}' updated for user '{user.username}'")
            return jsonify(task.to_dictionary())

        elif request.method == 'DELETE':
            db.session.delete(task)
            db.session.commit()
            logging.info(f"Task '{id}' deleted for user '{user.username}'")
            return '', 204

    except Exception as e:
        logging.error(f"Error in task modification: {e}")
        db.session.rollback()
        return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
