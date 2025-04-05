from pymongo import MongoClient

client = MongoClient("mongodb+srv://ammar:ObxTTUFj8gCDJek7@cluster0.o2qwc.mongodb.net/")  
db = client["appDB"]
users_collection = db["users"]
notes_collection = db["notes"]
files_collection = db['files']
history_collection = db['history']
images_collection = db['images']