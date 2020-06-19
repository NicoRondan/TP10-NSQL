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

def get_users():
    db = connect_db()
    users = db.users
    #Obtener todos menos a darth vader
    result = users.find({'username': {'$ne': 'Darth Vader' }}, {'_id': 0, 'password': 0})
    return result

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

def get_assets(public_key, criterion):
    #Obtener los activos
    transactions = []
    #Obtener outputs sin gastar del respectivo user
    outputs = bdb.outputs.get(public_key, False)
    for item in outputs:
        #Recuperar la transacción en base al id de la transaccion del output
        item["transaction"] = bdb.transactions.retrieve(txid=item["transaction_id"])
        #Si no hay metadata quiere decir que es una transaccion de moneda
        if item["transaction"]["metadata"] == None and criterion == 'coins' :
            transactions.append(item)
        elif item["transaction"]["metadata"] != None and criterion == 'weapons':
            transactions.append(item)
    return transactions

def get_galactic_coins(public_key):
    transactions_coins = get_assets(public_key, "coins")
    value = 0
    for element in transactions_coins:
        outputs = element["transaction"]["outputs"]
        #Posicion de la transaccion del user
        output = outputs[element["output_index"]]
        #Sumar el valor del amount por cada transaccion
        value += int(output["amount"])
    return value

def get_weapons(public_key):
    transactions_weapons = get_assets(public_key, 'weapons')
    #print(transactions_weapons)
    weapons = []
    for item in transactions_weapons:
        if item["transaction"]["operation"] != 'CREATE':
            id = item["transaction"]["asset"]["id"]
            data = bdb.transactions.get(asset_id=id, operation='CREATE')
            #print(data)
            data = data[0]["asset"]
            asset_id = item["transaction"]["asset"]["id"]
        else:
            data = item["transaction"]["asset"]
            asset_id = item["transaction"]["id"]
        #Obtener cantidad de armas
        outputs = item["transaction"]["outputs"]
        output =  outputs[item["output_index"]]
        amount = int(output["amount"])
        #Generar arma 
        weapon = {
            "id":asset_id,
            "data":data["data"],
            "amount":amount
        }
        #En caso de que el arma ya esté en la lista, se suman las cantidades
        if weapon not in weapons:
            weapons.append(weapon)
        else:
            for element in weapons:
                if (element["id"] == weapon["id"]):
                    element["amount"] = element["amount"] + amount
                    break
    return weapons

def transfer_coins(user1,user2,coins):
    user2 = get_user_by_name(user2)
    transactions_coins = get_assets(user1['public_key'],'coins')
    lost_coins = int(coins)
    i = 0
    while lost_coins != 0 and i < len(transactions_coins):
        item = transactions_coins[i]
        outputs = item["transaction"]["outputs"]
        output = outputs[item["output_index"]]
        amount = int(output["amount"])

        '''Iniciar transferencia'''
        transfer_input = {
                'fulfillment': output['condition']['details'],
                'fulfills': {
                'output_index': item["output_index"],
                'transaction_id': item["transaction_id"],
            },
                'owners_before': output['public_keys'],
            }
        if (item["transaction"]["operation"] == 'CREATE'):
            transfer_asset = {
            'id': item["transaction"]["id"],
            }
        else:
            transfer_asset = {
            'id': item["transaction"]["asset"]["id"],
            }    

        if (amount > lost_coins):
            '''Preparar transferencia'''
            prepared_transfer_tx = bdb.transactions.prepare(
            operation='TRANSFER',
            asset=transfer_asset,
            inputs=transfer_input,
            recipients=[([user2['public_key']], lost_coins), ([user1['public_key']], amount - lost_coins )]
            )
            #Firmar
            fulfilled_transfer_tx = bdb.transactions.fulfill(prepared_transfer_tx, private_keys=user1['private_key'])
            #Enviar nodo a bigchaindb
            bdb.transactions.send_commit(fulfilled_transfer_tx)

            lost_coins = 0
        #En caso de que se entreguen todos los coins disponibles
        elif (amount == lost_coins):
            prepared_transfer_tx = bdb.transactions.prepare(
            operation='TRANSFER',
            asset=transfer_asset,
            inputs=transfer_input,
            recipients=[([user2['public_key']], lost_coins)]
            )

            fulfilled_transfer_tx = bdb.transactions.fulfill(prepared_transfer_tx, private_keys=user1['private_key'])

            bdb.transactions.send_commit(fulfilled_transfer_tx)

            lost_coins = 0
        else:
            prepared_transfer_tx = bdb.transactions.prepare(
            operation='TRANSFER',
            asset=transfer_asset,
            inputs=transfer_input,
            recipients=[([user2['public_key']], amount)]
            )

            fulfilled_transfer_tx = bdb.transactions.fulfill(prepared_transfer_tx, private_keys=user1['private_key'])

            bdb.transactions.send_commit(fulfilled_transfer_tx)

            lost_coins = lost_coins - amount
        i += 1

def transfer_weapon (user, id_weapon):
    darth_vader = get_user_by_name('Darth Vader')
    transactions_weapons = get_assets(darth_vader['public_key'], 'weapons')
    metadata = {"type":"weapon"}
    
    for item in transactions_weapons:
        
        operation = item["transaction"]["operation"]
        
        if (operation == 'CREATE' and  item["transaction"]["id"] == id_weapon) or (operation == 'TRANSFER' and item["transaction"]["asset"]["id"] == id_weapon):
            outputs = item["transaction"]["outputs"]
            output = outputs[item["output_index"]]
            amount = int(output["amount"])

            '''iniciar transferencia'''
            transfer_input = {
                    'fulfillment': output['condition']['details'],
                    'fulfills': {
                    'output_index': item["output_index"],
                    'transaction_id': item["transaction_id"],
                },
                    'owners_before': output['public_keys'],
                }

            if (operation == 'CREATE'):
                transfer_asset = {
                'id': item["transaction"]["id"],
                }
            else:
                transfer_asset = {
                'id': item["transaction"]["asset"]["id"],
                }    

            if (amount == 1):
                prepared_transfer_tx = bdb.transactions.prepare(
                operation='TRANSFER',
                asset=transfer_asset,
                inputs=transfer_input,
                metadata=metadata,
                recipients=[([user['public_key']], amount)]
                )

                fulfilled_transfer_tx = bdb.transactions.fulfill(prepared_transfer_tx, private_keys=darth_vader['private_key'])
                bdb.transactions.send_commit(fulfilled_transfer_tx)
            else:
                prepared_transfer_tx = bdb.transactions.prepare(
                operation='TRANSFER',
                asset=transfer_asset,
                inputs=transfer_input,
                metadata=metadata,
                recipients=[([user['public_key']], 1),([darth_vader['public_key']], amount - 1)]
                )

                fulfilled_transfer_tx = bdb.transactions.fulfill(prepared_transfer_tx, private_keys=darth_vader['private_key'])
                bdb.transactions.send_commit(fulfilled_transfer_tx)

def add_weapon(darth_vader, name, price, amount):
    weapon = {
        "data": {
            "name": name,
            "price": price
        }
    }
    metadata = {'type': 'weapon'}
    #Preparamos la transacción
    prepared_creation_tx = bdb.transactions.prepare(
    operation='CREATE',
    signers=darth_vader['public_key'],
    recipients=[([darth_vader['public_key']], int(amount))],
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

def initialize():
    db = connect_db()
    users = db.users
    #users.drop()
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
            recipients=[([darth_vader['public_key']], 7)],
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