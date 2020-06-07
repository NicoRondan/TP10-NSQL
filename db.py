from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair
from bson.objectid import ObjectId
from pymongo import MongoClient
import bcrypt
import json


#BigchainDB server
URL = 'https://test.ipdb.io'
bdb = BigchainDB(URL)

def connect_db():
    try:
        client = MongoClient(host='db', port=27017)
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
    #Generar claves
    new_user = generate_keypair()
    #asignar al user
    user['public_key'] = new_user.public_key
    user['private_key'] = new_user.private_key
    users = db.users
    users.insert_one(user)
    #Retornar claves para la session
    dt = users.find({})
    print(dt)
    return user['public_key'], user['private_key']

def initialize():
    db = connect_db()
    users = db.users
    users.drop()
    if users.count() == 0:
        try:
            #Insertar archivos json contenidos en users.json
            with open('users.json', "r", encoding='utf-8') as file:
                data = json.load(file)
            for element in data:
                #Generamos claves
                element_keys = generate_keypair()
                #Asignamos
                element['public_key'] = element_keys.public_key
                element['private_key'] = element_keys.private_key  
                #Hasheamos el password
                hashpass = bcrypt.hashpw(element['password'].encode('utf-8'), bcrypt.gensalt())
                element['password'] = hashpass
            #Guardamos en la base de datos
            users.insert_many(data)
        except Exception as err:
            print("An exception occurred :", err)