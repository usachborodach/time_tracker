import click
from flask import Flask
from pymongo import ASCENDING

from .extensions import get_db


def register_cli(app: Flask) -> None:
    @app.cli.command('create-index')
    def create_index():
        """Создаёт уникальный индекс по date в коллекции days."""
        db = get_db()
        db.days.create_index([("date", ASCENDING)], unique=True)
        click.echo("Индекс создан")