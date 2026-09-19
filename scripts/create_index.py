"""Standalone-вариант создания индекса (без Flask)."""
import os
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/tracker'))
db = client.get_database()
db.days.create_index([("date", ASCENDING)], unique=True)
print("Индекс создан")