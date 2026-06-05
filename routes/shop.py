from flask import Blueprint, render_template, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from db import get_db
shop_bp = Blueprint('shop', __name__)
def parse_user(identity):
    if not identity: return None
    parts=identity.split('|',2)
    if len(parts)!=3: return None
    return {'id':int(parts[0]),'role':parts[1],'name':parts[2]}
@shop_bp.route('/')
def home():
    user=None
    try:
        verify_jwt_in_request(optional=True)
        user=parse_user(get_jwt_identity())
    except: pass
    db=get_db(); cur=db.cursor(dictionary=True)
    search=request.args.get('search','')
    category=request.args.get('category','all')
    query='SELECT * FROM products WHERE 1=1'
    params=[]
    if search:
        query+=' AND (name LIKE %s OR description LIKE %s)'
        params+=[f'%{search}%',f'%{search}%']
    if category!='all':
        query+=' AND category=%s'
        params.append(category)
    query+=' ORDER BY created_at DESC'
    cur.execute(query,params)
    products=cur.fetchall()
    cur.execute('SELECT DISTINCT category FROM products ORDER BY category')
    categories=[r['category'] for r in cur.fetchall()]
    cart_count=0
    if user:
        cur.execute('SELECT SUM(quantity) as c FROM cart WHERE user_id=%s',(user['id'],))
        r=cur.fetchone(); cart_count=r['c'] or 0
    return render_template('home.html',products=products,categories=categories,
        user=user,cart_count=cart_count,search=search,current_category=category)
@shop_bp.route('/product/<int:pid>')
def product_detail(pid):
    user=None
    try:
        verify_jwt_in_request(optional=True)
        user=parse_user(get_jwt_identity())
    except: pass
    db=get_db(); cur=db.cursor(dictionary=True)
    cur.execute('SELECT * FROM products WHERE id=%s',(pid,))
    product=cur.fetchone()
    if not product: return 'Product not found',404
    cart_count=0
    if user:
        cur.execute('SELECT SUM(quantity) as c FROM cart WHERE user_id=%s',(user['id'],))
        r=cur.fetchone(); cart_count=r['c'] or 0
    return render_template('product.html',product=product,user=user,cart_count=cart_count)
