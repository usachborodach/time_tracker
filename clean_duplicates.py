import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/tracker'))
db = client.get_database()
collection = db.days

# Находим все даты, у которых больше одного документа
pipeline = [
    {"$group": {"_id": "$date", "count": {"$sum": 1}, "ids": {"$push": "$_id"}}},
    {"$match": {"count": {"$gt": 1}}}
]
duplicates = collection.aggregate(pipeline)

for dup in duplicates:
    date = dup['_id']
    ids = dup['ids']
    # Оставляем первый документ (самый старый по _id), остальные удаляем
    keep_id = ids[0]
    delete_ids = ids[1:]
    result = collection.delete_many({"_id": {"$in": delete_ids}})
    print(f"Дата {date}: удалено {result.deleted_count} дубликатов, оставлен {keep_id}")

print("Готово.")