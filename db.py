from pymongo import MongoClient
import json
from bson.objectid import ObjectId

def connect_db():
    try:
        client = MongoClient(host='localhost', port=27017)
        db = client["blockchainDB"]
        return db
    except Exception as err:
        print("An exception occurred :", err)
        
def existing_user(username):
    db = connect_db()
    users = db.users
    existing_user = users.find_one({'name': username})
    return existing_user

def add_user(user):
    db = connect_db()
    users = db.users
    users.insert_one(user)