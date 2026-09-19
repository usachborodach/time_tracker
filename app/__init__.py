import logging
import time

from flask import Flask, request, session
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import get_config
from .extensions import init_extensions
from .auth import auth_bp
from .main import main_bp
from .cli import register_cli


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    # ProxyFix для корректного remote_addr за nginx
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    _setup_logging(app)
    init_extensions(app)

    # Блюпринты
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # CLI
    register_cli(app)

    # Хуки запросов
    _register_request_hooks(app)
    _register_error_handlers(app)

    return app


def _setup_logging(app: Flask) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()],
    )


def _register_request_hooks(app: Flask) -> None:
    @app.before_request
    def before_request():
        request.start_time = time.time()
        session.permanent = True

    @app.after_request
    def after_request(response):
        if hasattr(request, 'start_time'):
            elapsed = time.time() - request.start_time
            app.logger.info(
                "Request: %s %s IP: %s Status: %s Time: %.3fs",
                request.method, request.path,
                request.remote_addr, response.status_code, elapsed,
            )
        return response


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return e

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.exception("Unhandled exception occurred")
        return "Internal Server Error", 500