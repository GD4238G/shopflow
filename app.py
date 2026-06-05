from flask import Flask, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import os
load_dotenv()
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET','shopflow-secret')
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_SECURE'] = False
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
bcrypt  = Bcrypt(app)
jwt     = JWTManager(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["300 per hour"])
from routes.auth  import auth_bp
from routes.shop  import shop_bp
from routes.cart  import cart_bp
from routes.admin import admin_bp
app.register_blueprint(auth_bp,  url_prefix='/auth')
app.register_blueprint(shop_bp,  url_prefix='/shop')
app.register_blueprint(cart_bp,  url_prefix='/cart')
app.register_blueprint(admin_bp, url_prefix='/admin')
@app.route('/')
def index():
    return redirect(url_for('shop.home'))
@jwt.unauthorized_loader
def unauthorized(msg):
    return redirect(url_for('auth.login'))
@jwt.expired_token_loader
def expired(jwt_header, jwt_data):
    return redirect(url_for('auth.login'))
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
