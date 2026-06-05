from flask import Blueprint, render_template, request, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db
cart_bp = Blueprint('cart', __name__)
@cart_bp.route('/')
@jwt_required()
def view_cart():
    user=get_jwt_identity(); db=get_db(); cur=db.cursor(dictionary=True)
    cur.execute('''SELECT c.id,c.quantity,p.name,p.price,p.image_url,p.id as product_id,
        (c.quantity*p.price) as subtotal FROM cart c JOIN products p ON c.product_id=p.id
        WHERE c.user_id=%s''',(user['id'],))
    items=cur.fetchall()
    total=sum(i['subtotal'] for i in items)
    cur.execute('SELECT SUM(quantity) as c FROM cart WHERE user_id=%s',(user['id'],))
    cart_count=cur.fetchone()['c'] or 0
    return render_template('cart.html',items=items,total=total,user=user,cart_count=cart_count)
@cart_bp.route('/add/<int:pid>', methods=['POST'])
@jwt_required()
def add_to_cart(pid):
    user=get_jwt_identity(); qty=int(request.form.get('quantity',1))
    db=get_db(); cur=db.cursor()
    cur.execute('SELECT id,quantity FROM cart WHERE user_id=%s AND product_id=%s',(user['id'],pid))
    existing=cur.fetchone()
    if existing:
        cur.execute('UPDATE cart SET quantity=%s WHERE id=%s',(existing[1]+qty,existing[0]))
    else:
        cur.execute('INSERT INTO cart (user_id,product_id,quantity) VALUES (%s,%s,%s)',(user['id'],pid,qty))
    db.commit()
    return redirect(url_for('cart.view_cart'))
@cart_bp.route('/update/<int:cid>', methods=['POST'])
@jwt_required()
def update_cart(cid):
    user=get_jwt_identity(); qty=int(request.form.get('quantity',1))
    db=get_db(); cur=db.cursor()
    if qty<=0:
        cur.execute('DELETE FROM cart WHERE id=%s AND user_id=%s',(cid,user['id']))
    else:
        cur.execute('UPDATE cart SET quantity=%s WHERE id=%s AND user_id=%s',(qty,cid,user['id']))
    db.commit()
    return redirect(url_for('cart.view_cart'))
@cart_bp.route('/remove/<int:cid>', methods=['POST'])
@jwt_required()
def remove_from_cart(cid):
    user=get_jwt_identity(); db=get_db(); cur=db.cursor()
    cur.execute('DELETE FROM cart WHERE id=%s AND user_id=%s',(cid,user['id']))
    db.commit()
    return redirect(url_for('cart.view_cart'))
@cart_bp.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    user=get_jwt_identity(); address=request.form.get('address','').strip()
    if not address: return redirect(url_for('cart.view_cart'))
    db=get_db(); cur=db.cursor(dictionary=True)
    cur.execute('''SELECT c.quantity,p.price,p.id as product_id FROM cart c
        JOIN products p ON c.product_id=p.id WHERE c.user_id=%s''',(user['id'],))
    items=cur.fetchall()
    if not items: return redirect(url_for('cart.view_cart'))
    total=sum(i['quantity']*i['price'] for i in items)
    cur2=db.cursor()
    cur2.execute('INSERT INTO orders (user_id,total_amount,address) VALUES (%s,%s,%s)',(user['id'],total,address))
    db.commit(); order_id=cur2.lastrowid
    for item in items:
        cur2.execute('INSERT INTO order_items (order_id,product_id,quantity,price) VALUES (%s,%s,%s,%s)',
            (order_id,item['product_id'],item['quantity'],item['price']))
        cur2.execute('UPDATE products SET stock=stock-%s WHERE id=%s',(item['quantity'],item['product_id']))
    cur2.execute('DELETE FROM cart WHERE user_id=%s',(user['id'],))
    db.commit()
    return redirect(url_for('cart.orders'))
@cart_bp.route('/orders')
@jwt_required()
def orders():
    user=get_jwt_identity(); db=get_db(); cur=db.cursor(dictionary=True)
    cur.execute('''SELECT o.*,COUNT(oi.id) as item_count FROM orders o
        LEFT JOIN order_items oi ON o.id=oi.order_id
        WHERE o.user_id=%s GROUP BY o.id ORDER BY o.created_at DESC''',(user['id'],))
    orders=cur.fetchall()
    cur.execute('SELECT SUM(quantity) as c FROM cart WHERE user_id=%s',(user['id'],))
    cart_count=cur.fetchone()['c'] or 0
    return render_template('orders.html',orders=orders,user=user,cart_count=cart_count)
