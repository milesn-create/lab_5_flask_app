from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, User
from validation import validate_username, validate_password, validate_name

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        
        user = User.query.filter_by(login=login).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['login'] = user.login
            session['role'] = user.role
            session['first_name'] = user.first_name  
            session['last_name'] = user.last_name   
            session['user_name'] = user.full_name
            flash('Вы успешно вошли в систему.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль.', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему.', 'warning')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        user = User.query.get(session['user_id'])
        
        if not user.check_password(old_password):
            flash('Неверный старый пароль.', 'danger')
        else:
            # Используем вашу функцию validate_password
            password_errors = validate_password(new_password, confirm_password)
            if password_errors:
                for error in password_errors:
                    flash(error, 'danger')
            else:
                user.set_password(new_password)
                db.session.commit()
                flash('Пароль успешно изменён.', 'success')
                return redirect(url_for('index'))
    
    return render_template('change_password.html')