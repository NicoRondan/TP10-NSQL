from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, flash, session
from db import existing_user, add_user, initialize, get_galactic_coins, get_users, get_weapons, transfer_coins, get_user_by_name, transfer_weapon, add_weapon
import bcrypt


app = Flask(__name__)

"""Clave necesaria para poder utilizar flash"""
app.secret_key = 'clave_secreta'


@app.route('/initialize_db', methods=['GET'])
@app.before_first_request
def initialize_db():
    initialize()

@app.route('/')
def index():
    #En caso de que el usuario no haya iniciado sesion
    if 'public_key' not in session or session['public_key'] == None:
        return redirect(url_for('login'))
    else:
        #Obtener monedas del user
        coins = get_galactic_coins(session['public_key'])
        if session['username'] == 'Darth Vader':
            #Users para transferir coins
            users = get_users()
            #Armas para la venta
            weapons = get_weapons(session['public_key'])
            return render_template('index.html', users=users, coins=coins, weapons=weapons, isAdmin=True)
        else:
            darth_vader = get_user_by_name('Darth Vader')
            weapons = get_weapons(darth_vader['public_key'])
            #Renderizar index
            return render_template('index.html', coins=coins, weapons=weapons, isAdmin=False)

@app.route('/transfer-coins', methods=['POST'])
def transfer_galactic_coins():
    username = request.form.get('users')
    coins = request.form.get('amount')
    user_transfer = {
        'public_key': session['public_key'],
        'private_key': session['private_key']
    }
    transfer_coins(user_transfer, username, coins)
    return redirect(url_for('index'))

@app.route('/buy-weapon/<id>/<coins>/<price>', methods=['GET'])
def buy_weapon(id, coins, price):
    if (int(coins) < int(price)):
        flash('Insufficient Galactic Coins!')
        return redirect(url_for('index'))
    else:
        user_transfer = {
        'public_key': session['public_key'],
        'private_key': session['private_key']
        }
        #Pagamos
        transfer_coins(user_transfer, 'Darth Vader', price)
        #Transferimos arma
        transfer_weapon(user_transfer, id)
        flash('Weapon Adquired!')
        return redirect(url_for('user_weapons'))

@app.route('/add-weapon', methods=['GET', 'POST'])
def new_weapon():
    if request.method == 'POST':
        #Obtener datos
        name = request.form.get('name')
        price = request.form.get('price')
        amount = request.form.get('amount')
        darth_vader = {
            'public_key': session['public_key'],
            'private_key': session['private_key']
        }
        try:
            add_weapon(darth_vader, name, price, amount)
            flash('Weapon Added Successfully!')
            return redirect(url_for('index'))
        except Exception as err:
            print("An exception occurred :", err)
            flash('Error...')
    return render_template('add-weapon.html')


@app.route('/user-weapons', methods=['GET'])
def user_weapons():
    #Armas del user
    weapons = get_weapons(session['public_key'])
    #renderizar armas de user
    return render_template('user-weapons.html', weapons=weapons)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        #Obtener datos
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        #Verificar si existe el usuario
        login_user = existing_user(username)
        if login_user:
            if bcrypt.hashpw(password, login_user['password']) == login_user['password']:
                session['username'] = username
                session['public_key'] = login_user['public_key']
                session['private_key'] = login_user['private_key']
                flash('Hello, ' + session['username'] + '!')
                return redirect(url_for('index'))
        flash('Invalid username/password combination')
    return render_template('login.html')
            

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        #Obtener datos
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        #Verificar si existe el usuario
        user = existing_user(username)
        if user is None:
            #Hasheamos el password
            hashpass = bcrypt.hashpw(password, bcrypt.gensalt())
            #Generar usuario
            user = {
                'username': username,
                'password': hashpass
            }
            #Agregar user a bbdd
            public_key, private_key = add_user(user)
            #asignar a la session
            session['username'] = username
            session['public_key'] = public_key
            session['private_key'] = private_key
            return redirect(url_for('index'))
        #En caso de que exista el usuario
        flash('That username already exists!')
    #Si el method es GET
    return render_template('register.html')
    
            

@app.route('/logout')
def logout():
    session['username'] = None
    session['public_key'] = None
    session['private_key'] = None
    return redirect(url_for('index'))


#En caso de error de ruta
@app.errorhandler(404)
def not_found(error=None):
    response = jsonify({
        'message': 'Resource Not Found: ' + request.url,
        'status': 404 
    })
    response.status_code = 404
    return response


if __name__ == "__main__":
    app.run(host='src', port='5000', debug=True)