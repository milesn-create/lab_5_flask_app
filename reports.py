from flask import Blueprint, render_template, request, session, Response
from models import db, VisitLog, User
from decorators import check_rights
from sqlalchemy import func, desc, case
import csv
from io import StringIO
#ЧАСТЬ 3: СТАТИСТИЧЕСКИЕ ОТЧЁТЫ
reports_bp = Blueprint('reports', __name__, url_prefix='/reports')
# Функциональность отчётов в отдельном модуле (Blueprint)
#Подключение в app.py
#from reports import reports_bp
#app.register_blueprint(reports_bp)

#+ Главная страница журнала посещений
# + Пагинация записей 
#Отчёт по страницам + CSV
@reports_bp.route('/visit-logs')
@check_rights('view_own_logs')
def visit_logs():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    # Админ видит все логи
    if session.get('role') == 'admin':
        query = VisitLog.query.order_by(VisitLog.created_at.desc())
        total = VisitLog.query.count()
    else:
        # Обычный пользователь видит ТОЛЬКО свои посещения
        query = VisitLog.query.filter(
            VisitLog.user_id == session['user_id']
        ).order_by(VisitLog.created_at.desc())
        total = query.count()
    
    logs = query.offset(offset).limit(per_page).all()
    
    logs_list = []
    for idx, log in enumerate(logs, start=offset + 1):
        user_name = log.user.full_name if log.user else "Неаутентифицированный пользователь"
        logs_list.append({
            'num': idx,
            'user': user_name,
            'path': log.path,
            'date': log.created_at.strftime('%d.%m.%Y %H:%M:%S')
        })
    
    return render_template('visit_logs.html', logs=logs_list, page=page, total=total, per_page=per_page)

#Отчёт по страницам
@reports_bp.route('/stats/pages')
@check_rights('view_stats')
def stats_pages():
    stats = db.session.query(
        VisitLog.path,
        func.count(VisitLog.id).label('count')
    ).group_by(VisitLog.path).order_by(desc('count')).all()
    
    return render_template('stats_pages.html', stats=stats)


@reports_bp.route('/stats/pages/export')
@check_rights('export_csv')
def export_pages_csv():
    stats = db.session.query(
        VisitLog.path,
        func.count(VisitLog.id).label('count')
    ).group_by(VisitLog.path).order_by(desc('count')).all()
    
    si = StringIO()
    cw = csv.writer(si)  # Создаём CSV-писатель
    cw.writerow(['№', 'Страница', 'Количество посещений'])  # Заголовки с номером
    
    for idx, (path, count) in enumerate(stats, start=1):  # idx - порядковый номер (начинаем с 1)
        cw.writerow([idx, path, count])  # Записываем строку: номер, страница, количество
    
    output = si.getvalue()
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=pages_stats.csv'}
    )


@reports_bp.route('/stats/users')
@check_rights('view_stats')
def stats_users():
    # Получаем статистику по пользователям
    stats = db.session.query(
        case(
            (User.id.is_(None), 'Неаутентифицированный пользователь'),
            else_=func.concat(User.first_name, ' ', User.last_name)
        ).label('user_name'),
        func.count(VisitLog.id).label('count')
    ).outerjoin(VisitLog, User.id == VisitLog.user_id).group_by(User.id).order_by(desc('count')).all()
    
    # Преобразуем в список кортежей для шаблона
    stats_list = [(user_name, count) for user_name, count in stats]
    
    return render_template('stats_users.html', stats=stats_list)


@reports_bp.route('/stats/users/export')
@check_rights('export_csv')
def export_users_csv():
    stats = db.session.query(
        case(
            (User.id.is_(None), 'Неаутентифицированный пользователь'),
            else_=func.concat(User.first_name, ' ', User.last_name)
        ).label('user_name'),
        func.count(VisitLog.id).label('count')
    ).outerjoin(VisitLog, User.id == VisitLog.user_id).group_by(User.id).order_by(desc('count')).all()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['№', 'Пользователь', 'Количество посещений'])  # Заголовки с номером
    
    for idx, (user_name, count) in enumerate(stats, start=1):  # idx - порядковый номер
        cw.writerow([idx, user_name, count])
    
    output = si.getvalue()
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=users_stats.csv'}
    )