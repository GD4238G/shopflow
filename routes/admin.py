from flask import Blueprint, render_template, request, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db
admin_bp = Blueprint('admin', __name__)
def parse_user(identity):
    parts=identity.split('|',2)
    return {'id':int(parts[0]),'role':parts[1],'name':parts[2]}
def check_admin():
    user=parse_user(get_jwt_identity())
    return user if user and user.get('role')=='admin' else None
@admin_bp.route('/dashboard')
@jwt_required()
def dashboard():
    user=check_admin()
    if not user: return redirect(url_for('auth.login'))
    db=get_db(); cur=db.cursor(dictionary=True)
    cur.execute('SELECT COUNT(*) as c FROM users WHERE role="user"'); total_users=cur.fetchone()['c']
    cur.execute('SELECT COUNT(*) as c FROM products'); total_products=cur.fetchone()['c']
    cur.execute('SELECT COUNT(*) as c FROM orders'); total_orders=cur.fetchone()['c']
    cur.execute('SELECT SUM(total_amount) as rev FROM orders WHERE status!="cancelled"')
    revenue=cur.fetchone()['rev'] or 0
    cur.execute('SELECT o.*,u.name as user_name FROM orders o JOIN users u ON o.user_id=u.id ORDER BY o.created_at DESC LIMIT 10')
    recent_orders=cur.fetchall()
    cur.execute('SELECT * FROM products ORDER BY stock ASC LIMIT 5')
    low_stock=cur.fetchall()
    return render_template('admin.html',user=user,total_users=total_users,total_products=total_products,total_orders=total_orders,revenue=revenue,recent_orders=recent_orders,low_stock=low_stock)
@admin_bp.route('/products')
@jwt_required()
def products():
    user=check_admin()
    if not user: return redirect(url_for('auth.login'))
    db=get_db(); cur=db.cursor(dictionary=True)
    cur.execute('SELECT * FROM products ORDER BY created_at DESC')
    products=cur.fetchall()
    return render_template('admin_products.html',user=user,products=products)
@admin_bp.route('/products/add', methods=['POST'])
@jwt_required()
def add_product():
    user=check_admin()
    if not user: return redirect(url_for('auth.login'))
    db=get_db(); cur=db.cursor()
    cur.execute('INSERT INTO products (name,description,price,stock,category,image_url) VALUES (%s,%s,%s,%s,%s,%s)',
        (request.form['name'],request.form['description'],request.form['price'],
         request.form['stock'],request.form['category'],request.form.get('image_url','')))
    db.commit()
    return redirect(url_for('admin.products'))
@admin_bp.route('/products/edit/<int:pid>', methods=['POST'])
@jwt_required()
def edit_product(pid):
    user=check_admin()
    if not user: return redirect(url_for('auth.login'))
    db=get_db(); cur=db.cursor()
    cur.execute('UPDATE products SET name=%s,description=%s,price=%s,stock=%s,category=%s,image_url=%s WHERE id=%s',
        (request.form['name'],request.form['description'],request.form['price'],
         request.form['stock'],request.form['category'],request.form.get('image_url',''),pid))
    db.commit()
    return redirect(url_for('admin.products'))
@admin_bp.route('/products/delete/<int:pid>', methods=['POST'])
@jwt_required()
def delete_product(pid):
    user=check_admin()
    if not user: return redirect(url_for('auth.login'))
    db=get_db(); cur=db.cursor()
    cur.execute('DELETE FROM products WHERE id=%s',(pid,))
    db.commit()
    return redirect(url_for('admin.products'))
@admin_bp.route('/users')
@jwt_required()
def users():
    user=check_admin()
    if not user: return redirect(url_for('auth.login'))
    db=get_db(); cur=db.cursor(dictionary=True)
    cur.execute('SELECT id,name,email,role,created_at FROM users ORDER BY created_at DESC')
    users=cur.fetchall()
    return render_template('admin_users.html',user=user,users=users)
@admin_bp.route('/users/delete/<int:uid>', methods=['POST'])
@jwt_required()
def delete_user(uid):
    user=check_admin()
    if not user: return redirect(url_for('auth.login'))
    db=get_db(); cur=db.cursor()
    cur.execute('DELETE FROM users WHERE id=%s AND role!="admin"',(uid,))
    db.commit()
    return redirect(url_for('admin.users'))
@admin_bp.route('/orders')
@jwt_required()
def all_orders():
    user=check_admin()
    if not user: return redirect(url_for('auth.login'))
    db=get_db(); cur=db.cursor(dictionary=True)
    cur.execute('SELECT o.*,u.name as user_name FROM orders o JOIN users u ON o.user_id=u.id ORDER BY o.created_at DESC')
    orders=cur.fetchall()
    return render_template('admin_orders.html',user=user,orders=orders)
@admin_bp.route('/orders/update/<int:oid>', methods=['POST'])
@jwt_required()
def update_order(oid):
    user=check_admin()
    if not user: return redirect(url_for('auth.login'))
    db=get_db(); cur=db.cursor()
    cur.execute('UPDATE orders SET status=%s WHERE id=%s',(request.form.get('status'),oid))
    db.commit()
    return redirect(url_for('admin.all_orders'))
