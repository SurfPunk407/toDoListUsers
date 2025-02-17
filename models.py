from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    tasks = db.relationship('Task', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    priority = db.Column(db.String(50), nullable=True)
    status = db.Column(db.Boolean, default=True)
    task_date = db.Column(db.String(20), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dictionary(self):
        return {
            "id": self.id,
            "task": self.task,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "task_date": self.task_date
        }