from flask import Blueprint, render_template, request, redirect, url_for, make_response
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies
from db import get_db
import mysql.connector
auth_bp = Blueprint('auth', __name__)
bcrypt  = Bcrypt()
@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    name=request.form.get('name','').strip()
    email=request.form.get('email','').strip().lower()
    password=request.form.get('password','')
    if not all([name,email,password]):
        return render_template('register.html', error='All fields required')
    if len(password) < 8:
        return render_template('register.html', error='Password must be 8+ characters')
    hashed=bcrypt.generate_password_hash(password).decode('utf-8')
    try:
        db=get_db(); cur=db.cursor()
        cur.execute('INSERT INTO users (name,email,password) VALUES (%s,%s,%s)',(name,email,hashed))
        db.commit()
        return redirect(url_for('auth.login', success='Account created! Please login.'))
    except mysql.connector.IntegrityError:
        return render_template('register.html', error='Email already registered')
@auth_bp.route('/login', methods=['GET','POST'])
def login():
    success=request.args.get('success','')
    if request.method == 'GET':
        return render_template('login.html', success=success)
    email=request.form.get('email','').strip().lower()
    password=request.form.get('password','')
    if not all([email,password]):
        return render_template('login.html', error='All fields required')
    db=get_db(); cur=db.cursor(dictionary=True)
    cur.execute('SELECT * FROM users WHERE email=%s',(email,))
    user=cur.fetchone()
    if not user or not bcrypt.check_password_hash(user['password'],password):
        return render_template('login.html', error='Invalid email or password')
    identity = str(user['id'])+'|'+user['role']+'|'+user['name']
    token=create_access_token(identity=identity)
    dest=url_for('admin.dashboard') if user['role']=='admin' else url_for('shop.home')
    response=make_response(redirect(dest))
    set_access_cookies(response, token)
    return response
@auth_bp.route('/logout')
def logout():
    response=make_response(redirect(url_for('auth.login')))
    unset_jwt_cookies(response)
    return response
