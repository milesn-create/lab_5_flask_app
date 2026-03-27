import sqlite3
import hashlib
from datetime import datetime
from contextlib import contextmanager

DATABASE = 'users.db'


def init_db():
    """Инициализация базы данных"""
    with get_db_connection() as conn:
         # открываем соединение с БД через контекстный менеджер (автоматически закроется)
        cursor = conn.cursor()
        # создаём объект cursor — через него выполняются SQL-запросы

        # Создание таблицы ролей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            )
        ''')

        # Создание таблицы пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                last_name TEXT,
                first_name TEXT NOT NULL,
                middle_name TEXT,
                role_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES roles (id)
            )
        ''')

        # Добавление стандартных ролей, если их нет
        cursor.execute("SELECT COUNT(*) FROM roles")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO roles (name, description) VALUES (?, ?)",
                [
                    ('admin', 'Администратор системы'),
                    ('user', 'Обычный пользователь'),
                    ('guest', 'Гость (только просмотр)')
                ]
            )
            conn.commit()

        # Добавление демо-пользователей, если их нет
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            # Пароль для admin: Admin123
            admin_password_hash = hash_password('Admin123')
            # Пароль для user1: User12345
            user1_password_hash = hash_password('User12345')

            # Получаем ID ролей
            cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
            admin_role_result = cursor.fetchone()
            admin_role_id = admin_role_result[0] if admin_role_result else None

            cursor.execute("SELECT id FROM roles WHERE name = 'user'")
            user_role_result = cursor.fetchone()
            user_role_id = user_role_result[0] if user_role_result else None

            # Проверяем, что пользователи еще не существуют
            cursor.execute("SELECT username FROM users WHERE username IN ('admin', 'user1')")
            existing_users = [row[0] for row in cursor.fetchall()]

            if 'admin' not in existing_users:
                cursor.execute('''
                    INSERT INTO users 
                    (username, password_hash, first_name, last_name, role_id) 
                    VALUES (?, ?, ?, ?, ?)
                ''', ('admin', admin_password_hash, 'Админ', 'Администратор', admin_role_id))

            if 'user1' not in existing_users:
                cursor.execute('''
                    INSERT INTO users 
                    (username, password_hash, first_name, last_name, role_id) 
                    VALUES (?, ?, ?, ?, ?)
                ''', ('user1', user1_password_hash, 'Иван', 'Иванов', user_role_id))

        conn.commit()

# создаём объект cursor — через него выполняются SQL-запросы
@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к БД"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
         # ВАЖНО: yield возвращает conn наружу (в with)
        # и "замораживает" функцию до выхода из with
    finally:
        conn.close()


def hash_password(password):
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, password_hash):
    """Проверка пароля"""
    return hash_password(password) == password_hash


# CRUD операции для пользователей
def create_user(username, password, first_name, last_name=None, middle_name=None, role_id=None):
    """Создание нового пользователя"""
    password_hash = hash_password(password)
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash, last_name, first_name, 
                             middle_name, role_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, password_hash, last_name, first_name, middle_name, role_id, created_at))
        conn.commit()
        return cursor.lastrowid
     # возвращаем id созданного пользователя


def get_all_users():
    """Получение всех пользователей с информацией о роли"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, r.name as role_name 
            FROM users u 
            LEFT JOIN roles r ON u.role_id = r.id
            ORDER BY u.id
        ''')
        return cursor.fetchall()


def get_user_by_id(user_id):
    """Получение пользователя по ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, r.name as role_name 
            FROM users u 
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.id = ?
        ''', (user_id,))
        return cursor.fetchone()


def get_user_by_username(username):
    """Получение пользователя по имени пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, r.name as role_name 
            FROM users u 
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.username = ?
        ''', (username,))
        return cursor.fetchone()


def update_user(user_id, first_name, last_name=None, middle_name=None, role_id=None):
    """Обновление данных пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET last_name = ?, first_name = ?, middle_name = ?, role_id = ?
            WHERE id = ?
        ''', (last_name, first_name, middle_name, role_id, user_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_user(user_id):
    """Удаление пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        return cursor.rowcount > 0


def change_password(user_id, new_password):
    """Изменение пароля пользователя"""
    password_hash = hash_password(new_password)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET password_hash = ?
            WHERE id = ?
        ''', (password_hash, user_id))
        conn.commit()
        return cursor.rowcount > 0


# Операции для ролей
def get_all_roles():
    """Получение всех ролей"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM roles ORDER BY id')
        return cursor.fetchall()


def get_role_by_id(role_id):
    """Получение роли по ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM roles WHERE id = ?', (role_id,))
        return cursor.fetchone()