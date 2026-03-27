from functools import wraps
from flask import session, redirect, url_for, flash
import database

def login_required(f):
    """Декоратор для проверки аутентификации"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Для доступа к этой странице необходимо войти в систему', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def check_auth(username, password):
    """Проверка учетных данных"""
    user = database.get_user_by_username(username)
    if user and database.verify_password(password, user['password_hash']):
        return user
    return None

def login_user(user):
    """Вход пользователя в систему"""
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['first_name'] = user['first_name']
    session['last_name'] = user['last_name']

def logout_user():
    """Выход пользователя из системы"""
    session.clear()

def get_current_user():
    """Получение текущего пользователя"""
    if 'user_id' in session:
        return database.get_user_by_id(session['user_id'])
    return None