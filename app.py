from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, flash, session
from db import existing_user, add_user, initialize
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
    #Renderizar index
    return render_template('index.html')

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
                'name': username,
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