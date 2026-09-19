import os
os.environ.setdefault('SECRET_KEY', 'test')
os.environ.setdefault('USERNAME', 'admin')
os.environ.setdefault('PASSWORD_HASH', 'x')

from app import create_app


def test_app_creates():
    app = create_app()
    assert app is not None
    assert 'auth.login' in app.view_functions
    assert 'main.index' in app.view_functions