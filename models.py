from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
 #ЖУРНАЛ ПОСЕЩЕНИЙ (VISIT LOGS) ниже
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=True)
    middle_name = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(20), default='user')  # 'admin' или 'user'
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Связь с журналом посещений
    visits = db.relationship('VisitLog', back_populates='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}" if self.last_name else self.first_name
        if self.middle_name:
            name += f" {self.middle_name}"
        return name
    
    def __repr__(self):
        return f"<User {self.login}>"


class VisitLog(db.Model):
    __tablename__ = 'visit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Связь с пользователем
    user = db.relationship('User', back_populates='visits')
    
    def __repr__(self):
        return f"<VisitLog {self.path} by user {self.user_id}>"