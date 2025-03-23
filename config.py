from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")  
db = client["appDB"]
users_collection = db["users"]
notes_collection = db["notes"]