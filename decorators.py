from functools import wraps
from flask import session, flash, redirect, url_for

def check_rights(action):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Отладка
            print(f"DEBUG: action={action}, user_role={session.get('role')}")
            
            if 'user_id' not in session:
                flash('Пожалуйста, войдите в систему.', 'warning')
                return redirect(url_for('auth.login'))
            
            user_role = session.get('role', 'user')
            
            # Администратор имеет все права
            if user_role == 'admin':
                return func(*args, **kwargs)
            
            # Права обычного пользователя
            allowed_for_user = {
                'create': False,
                'edit': False,
                'delete': False,
                'view': False,
                'view_own_logs': True,
                'view_stats': False,
                'export_csv': False
            }
            
            # Проверка для действий с конкретным пользователем (edit, view, delete)
            if action in ['edit', 'view', 'delete']:
                user_id_from_url = kwargs.get('user_id')
                if user_id_from_url and user_id_from_url == session['user_id']:
                    return func(*args, **kwargs)
                else:
                    flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
                    return redirect(url_for('index'))
            
            # Для всех остальных действий
            if allowed_for_user.get(action, False):
                return func(*args, **kwargs)
            else:
                flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
                return redirect(url_for('index'))
        
        return wrapper
    return decorator