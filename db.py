from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair, CryptoKeypair
from bson.objectid import ObjectId
from pymongo import MongoClient
import bcrypt
import json


#BigchainDB server
URL = 'https://test.ipdb.io'
bdb = BigchainDB(URL)
#print(bdb.assets.get(search='20'))

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
    existing_user = users.find_one({'username': username})
    return existing_user

def get_user_by_name(name):
    db = connect_db()
    users = db.users
    #retornar solamente las keys
    user = users.find_one({'username': name}, {'_id': 0, 'public_key': 1, 'private_key': 2})
    return user

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
    return user['public_key'], user['private_key']

def get_galactic_coins(public_key):
    #Obtener los assets
    asset = bdb.assets.get(search='Galactic Coins')[0]
    transaction = bdb.transactions.get(asset_id=asset['id'])
    galactic_coins = None
    transaction_id = None
    output_index = None
    output = None
    index = 0
    for item in transaction[0]['outputs']:
        #Recorremos los outputs
        if public_key in item['public_keys']:
            output_index = index
            galactic_coins = item['amount']
            break
        if galactic_coins != None:
            transaction_id = item["id"]
            output = item["outputs"][output_index]
            break
        i =+ 1    
    obj = {
        'galactic_coins': galactic_coins,
        'transaction_id': transaction_id,
        'output_index': output_index,
        'output': output,
    }
    return obj

def initialize():
    db = connect_db()
    users = db.users
    #users.drop()#
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
                password = element['password'].encode('utf-8')
                hashpass = bcrypt.hashpw(password, bcrypt.gensalt())
                element['password'] = hashpass
            #Guardamos en la base de datos
            users.insert_many(data)
        except Exception as err:
            print("An exception occurred :", err)
        
        '''Pasamos a crear el activo de galactic coins'''
        asset = {
            'data': { 
                    'name': "Galactic Coins",
                },
        }
#

        #Obtenemos usuarios con sus respectivas keys
        darth_vader = get_user_by_name('Darth Vader')
        greedo = get_user_by_name('Greedo')
        din_djarin = get_user_by_name('Din Djarin')
        bobba_fett = get_user_by_name('Bobba Fett')

        #Preparamos la transacción
        prepared_galactic_coins_tx = bdb.transactions.prepare(
        operation='CREATE',
        signers=darth_vader['public_key'],
        recipients=[([bobba_fett['public_key']], 5), ([greedo['public_key']], 3), ([din_djarin['public_key']], 8), ([darth_vader['public_key']], 4)],
        asset=asset)

        #Completamos la transacción
        fulfilled_galactic_coins_tx = bdb.transactions.fulfill(
            prepared_galactic_coins_tx, 
            private_keys=darth_vader['private_key']
        )

        # Y enviamos el nodo a bigchaindb
        bdb.transactions.send_commit(fulfilled_galactic_coins_tx)
        
        ''' Cración de armas '''
        metadata = {'type': 'weapon'}
      
        with open('weapons.json', "r", encoding='utf-8') as f:
            weapons = json.load(f)
        for weapon in weapons:
            #Preparamos la transacción
            prepared_creation_tx = bdb.transactions.prepare(
            operation='CREATE',
            signers=darth_vader['public_key'],
            recipients=[([darth_vader['public_key']], 10)],
            asset=weapon,
            metadata=metadata
            )
            #Completamos la transacción
            fulfilled_creation_tx = bdb.transactions.fulfill(
            prepared_creation_tx,
            private_keys=darth_vader['private_key']
            )
            # Y enviamos el nodo a bigchaindb
            bdb.transactions.send_commit(fulfilled_creation_tx)










'''Iniciar transferencia'''
        # transfer_asset = {
        #     'id': fulfilled_galactic_coins_tx['id']
        # }
        # output_index = 0
        # output = fulfilled_galactic_coins_tx['outputs'][output_index]
        # transfer_input = {
        #     'fulfillment': output['condition']['details'],
        #     'fulfills': {
        #         'output_index': output_index,
        #         'transaction_id': transfer_asset['id']
        #     },
        #     'owners_before': output['public_keys']
        # }

        # #Preparamos la transferencia
        # prepared_transfer_tx = bdb.transactions.prepare(
        # operation='TRANSFER',
        # asset=transfer_asset,
        # inputs=transfer_input,
        # recipients=[([bobba_fett['public_key']], 5), ([greedo['public_key']], 3), ([din_djarin['public_key']], 8), ([darth_vader['public_key']], 4)]
        # )
        # #
        # #Completamos la transferencia
        # fulfilled_transfer_tx = bdb.transactions.fulfill(
        #     prepared_transfer_tx,
        #     private_keys=darth_vader['private_key'],
        # )

        # #Commiteamos
        # sent_transfer_tx = bdb.transactions.send_commit(fulfilled_transfer_tx)