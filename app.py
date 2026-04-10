from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import Config
from models import db, User, VisitLog
from auth import auth_bp
from reports import reports_bp
from decorators import check_rights
from validation import validate_username, validate_password, validate_name
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# Добавляем enumerate в шаблоны
app.jinja_env.globals.update(enumerate=enumerate)

# Инициализация БД
 # ← Здесь SQLAlchemy подключает драйвер
db.init_app(app)

# Регистрация Blueprint'ов
app.register_blueprint(auth_bp)
app.register_blueprint(reports_bp)

# Создание таблиц при первом запуске
with app.app_context():
    db.create_all()
    # Создание тестового администратора, если нет пользователей
    if User.query.count() == 0:
        admin = User(
            login='admin',
            first_name='Admin',
            last_name='Adminov',
            role='admin'
        )
        admin.set_password('Admin123')
        db.session.add(admin)
        
        user = User(
            login='user',
            first_name='User',
            last_name='Userov',
            role='user'
        )
        user.set_password('User123')
        db.session.add(user)
        
        db.session.commit()
        print("Тестовые пользователи созданы: admin/Admin123, user/User123")

#Автоматическое заполнение через before_request
@app.before_request
def log_visit():
    """Логирование всех посещений (кроме статики)"""
    if request.endpoint and not request.endpoint.startswith('static'):
        path = request.path
        user_id = session.get('user_id') if session.get('user_id') else None
        
        visit_log = VisitLog(
            path=path,
            user_id=user_id
        )
        db.session.add(visit_log)
        db.session.commit()


@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)


@app.route('/user/create', methods=['GET', 'POST'])
@check_rights('create')
def create_user():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form.get('last_name', '')
        middle_name = request.form.get('middle_name', '')
        role = request.form.get('role', 'user')
        
        # Валидация логина
        username_errors = validate_username(login)
        if username_errors:
            for error in username_errors:
                flash(error, 'danger')
            return render_template('user_form.html', user=request.form, is_edit=False)
        
        # Проверка на существующего пользователя
        if User.query.filter_by(login=login).first():
            flash('Пользователь с таким логином уже существует.', 'danger')
            return render_template('user_form.html', user=request.form, is_edit=False)
        
        # Валидация пароля
        password_errors = validate_password(password)
        if password_errors:
            for error in password_errors:
                flash(error, 'danger')
            return render_template('user_form.html', user=request.form, is_edit=False)
        
        # Валидация имени
        name_errors = validate_name('first_name', first_name)
        if name_errors:
            for error in name_errors:
                flash(error, 'danger')
            return render_template('user_form.html', user=request.form, is_edit=False)
        
        # Создание пользователя
        new_user = User(
            login=login,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            role=role
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Пользователь успешно создан.', 'success')
        return redirect(url_for('index'))
    
    return render_template('user_form.html', user=None, is_edit=False)


@app.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@check_rights('edit')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Обычный пользователь не может менять роль
        if session.get('role') == 'admin':
            user.role = request.form.get('role', user.role)
        
        user.first_name = request.form['first_name']
        user.last_name = request.form.get('last_name', '')
        user.middle_name = request.form.get('middle_name', '')
        
        # Валидация имени
        name_errors = validate_name('first_name', user.first_name)
        if name_errors:
            for error in name_errors:
                flash(error, 'danger')
            return render_template('user_form.html', user=user, is_edit=True)
        
        db.session.commit()
        flash('Данные пользователя обновлены.', 'success')
        return redirect(url_for('index'))
    
    return render_template('user_form.html', user=user, is_edit=True)


@app.route('/user/<int:user_id>/delete', methods=['POST'])
@check_rights('delete')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Нельзя удалить самого себя
    if user.id == session.get('user_id'):
        flash('Вы не можете удалить свою учётную запись.', 'danger')
        return redirect(url_for('index'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'Пользователь {user.full_name} удалён.', 'success')
    return redirect(url_for('index'))


@app.route('/user/<int:user_id>')
@check_rights('view')
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('view_user.html', user=user)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)