from pymongo import MongoClient, ASCENDING
client = MongoClient('mongodb://localhost:27017/tracker')
db = client.get_database()
db.days.create_index([("date", ASCENDING)], unique=True)