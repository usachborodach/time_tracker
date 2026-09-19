from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from pymongo import MongoClient

login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
mongo = MongoClient()  # реальный URI задаётся в init_extensions


def init_extensions(app) -> None:
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    limiter.init_app(app)

    # Mongo — единый клиент на процесс
    global mongo
    mongo = MongoClient(app.config['MONGO_URI'])


def get_db():
    return mongo.get_database()