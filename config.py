import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Для локальной разработки используем SQLite
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
    
    # Если используется PostgreSQL на Render, DATABASE_URL приходит в формате postgres://
    # SQLAlchemy требует postgresql://, поэтому заменяем
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False