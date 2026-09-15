import os
from datetime import datetime, time, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from pymongo import MongoClient
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from werkzeug.security import generate_password_hash, check_password_hash


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# MongoDB
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/tracker'))
db = client.get_database()
days_collection = db.days

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Простая модель пользователя (один пользователь)
class User(UserMixin):
    def __init__(self, username):
        self.id = username

# Загрузка пользователя (по id)
@login_manager.user_loader
def load_user(user_id):
    if user_id == os.getenv('USERNAME'):
        return User(user_id)
    return None

# Проверка пароля (простая, в реальном проекте используйте хеши)
PASSWORD_HASH = os.getenv('PASSWORD_HASH')
def verify_password(username, password):
    return (username == os.getenv('USERNAME') and
            check_password_hash(PASSWORD_HASH, password))

# Список доступных активностей
ACTIVITIES = [
    'Обзор задач',
    'Работал',
    'Кодил для себя',
    'Домашние задачи',
    'Залипал',
    'Спал',
    'Время с семьёй',
    'Время с Юлочкой',
    'Время с Ваней',
    'Время с Таней',    
]

# Часы, которые будут отображаться
HOURS = [
    '07:00', '08:00', '09:00', '10:00', '11:00', '12:00',
    '13:00', '14:00', '15:00', '16:00', '17:00',
    '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
]

# Функция создания документа дня
def create_day_record(date):
    hours_dict = {hour: '' for hour in HOURS}
    doc = {
        'date': datetime(date.year, date.month, date.day),
        'hours': hours_dict
    }
    days_collection.insert_one(doc)
    return doc

# Получить или создать запись за указанную дату
def get_or_create_day(date):
    # Преобразуем date в datetime (как хранится в БД)
    date_obj = datetime(date.year, date.month, date.day)
    
    # Пытаемся обновить или вставить документ атомарно
    result = days_collection.update_one(
        {'date': date_obj},
        {'$setOnInsert': {'hours': {hour: '' for hour in HOURS}}},
        upsert=True
    )
    # Возвращаем документ
    doc = days_collection.find_one({'date': date_obj})
    return doc

# Ежедневное создание записи на следующий день (запускается в 00:00)
def create_tomorrow_record():
    tomorrow = datetime.now().date() + timedelta(days=1)
    get_or_create_day(tomorrow)

# Инициализация планировщика
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=create_tomorrow_record,
    trigger=CronTrigger(hour=0, minute=0),
    id='create_daily_record',
    replace_existing=True
)
scheduler.start()

# Роуты
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_password(username, password):
            user = User(username)
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверный логин или пароль', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    # Получаем дату из параметра или сегодня
    date_str = request.args.get('date')
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            date_obj = datetime.now().date()
    else:
        date_obj = datetime.now().date()

    doc = get_or_create_day(date_obj)
    hours = doc['hours']
    return render_template('index.html',
                           date=date_obj,
                           hours=hours,
                           activities=ACTIVITIES,
                           hours_list=HOURS,
                           timedelta=timedelta)

@app.route('/update', methods=['POST'])
@login_required
def update():
    data = request.json
    date_str = data.get('date')
    hour = data.get('hour')
    activity = data.get('activity')

    if not date_str or not hour:
        return jsonify({'success': False, 'message': 'Недостаточно данных'}), 400

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Неверный формат даты'}), 400

    if hour not in HOURS:
        return jsonify({'success': False, 'message': 'Неверный час'}), 400

    if activity and activity not in ACTIVITIES:
        return jsonify({'success': False, 'message': 'Неверная активность'}), 400

    # Обновление в БД
    result = days_collection.update_one(
        {'date': datetime(date_obj.year, date_obj.month, date_obj.day)},
        {'$set': {f'hours.{hour}': activity}}
    )
    if result.matched_count:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Запись не найдена'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=False)