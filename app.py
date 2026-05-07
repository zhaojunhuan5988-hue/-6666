import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'db', 'factory_erp.db')

DEFAULT_USER = '默认用户'


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def gen_no(prefix):
    return prefix + datetime.now().strftime('%Y%m%d%H%M%S')


# ==================== 静态文件 ====================
@app.route('/')
def index():
    html_path = os.path.join(BASE_DIR, 'static', 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    resp = make_response(content)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(os.path.join(BASE_DIR, 'static'), path)


@app.route('/api/ping')
def ping():
    return jsonify({'status': 'ok'})


# ==================== 通用 CRUD 辅助 ====================
def crud_get(table, order_clause='ORDER BY id'):
    conn = get_db()
    rows = conn.execute(f'SELECT * FROM {table} {order_clause}').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


def crud_add(table, data, conn=None):
    fields = ', '.join(data.keys())
    placeholders = ', '.join(['?'] * len(data))
    vals = list(data.values())
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True
    cur = conn.execute(f'INSERT INTO {table} ({fields}) VALUES ({placeholders})', vals)
    if close_conn:
        conn.commit()
        conn.close()
    return cur.lastrowid


def crud_update(table, rid, data, conn=None):
    sets = ', '.join([f'{k}=?' for k in data.keys()])
    vals = list(data.values()) + [rid]
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True
    conn.execute(f'UPDATE {table} SET {sets} WHERE id=?', vals)
    if close_conn:
        conn.commit()
        conn.close()


def crud_delete(table, rid):
    conn = get_db()
    conn.execute(f'DELETE FROM {table} WHERE id=?', (rid,))
    conn.commit()
    conn.close()


# ==================== 1. 用户管理 ====================
@app.route('/api/users', methods=['GET'])
def list_users():
    conn = get_db()
    rows = conn.execute('SELECT id, username, name, role, phone, created_at FROM users ORDER BY id').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/users', methods=['POST'])
def add_user():
    import hashlib
    data = request.json
    data['password'] = hashlib.sha256(data.get('password', '123456').encode()).hexdigest()
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn = get_db()
        crud_add('users', data, conn)
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': '用户名已存在'}), 400
    finally:
        conn.close()
    return jsonify({'success': True})


# ==================== 2. 员工管理（+department）====================
@app.route('/api/employees', methods=['GET'])
def list_employees():
    conn = get_db()
    rows = conn.execute('SELECT * FROM employees ORDER BY id').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/employees', methods=['POST'])
def add_employee():
    data = request.json
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn = get_db()
        crud_add('employees', data, conn)
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': '工号已存在'}), 400
    finally:
        conn.close()
    return jsonify({'success': True})


@app.route('/api/employees/<int:eid>', methods=['PUT'])
def update_employee(eid):
    data = request.json
    conn = get_db()
    crud_update('employees', eid, data, conn)
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/employees/<int:eid>', methods=['DELETE'])
def delete_employee(eid):
    crud_delete('employees', eid)
    return jsonify({'success': True})


# ==================== 3. 客户管理 ====================
@app.route('/api/customers', methods=['GET'])
def list_customers():
    return crud_get('customers')


@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.json
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn = get_db()
        crud_add('customers', data, conn)
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': '客户编号已存在'}), 400
    finally:
        conn.close()
    return jsonify({'success': True})


@app.route('/api/customers/<int:cid>', methods=['PUT'])
def update_customer(cid):
    data = request.json
    conn = get_db()
    crud_update('customers', cid, data, conn)
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/customers/<int:cid>', methods=['DELETE'])
def delete_customer(cid):
    crud_delete('customers', cid)
    return jsonify({'success': True})


# ==================== 4. 销售订单 ====================
@app.route('/api/sales', methods=['GET'])
def list_sales():
    conn = get_db()
    rows = conn.execute('''
        SELECT s.*, c.name as customer_name
        FROM sales_orders s
        LEFT JOIN customers c ON c.id = s.customer_id
        ORDER BY s.id DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/sales', methods=['POST'])
def add_sale():
    data = request.json
    data['order_no'] = gen_no('SO')
    data['status'] = 'pending'
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn = get_db()
        crud_add('sales_orders', data, conn)
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': '订单号重复'}), 400
    finally:
        conn.close()
    return jsonify({'success': True})


@app.route('/api/sales/<int:sid>', methods=['PUT'])
def update_sale(sid):
    data = request.json
    conn = get_db()
    crud_update('sales_orders', sid, data, conn)
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/sales/<int:sid>/confirm', methods=['POST'])
def confirm_sale(sid):
    conn = get_db()
    conn.execute("UPDATE sales_orders SET status='confirmed' WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/sales/<int:sid>', methods=['DELETE'])
def delete_sale(sid):
    crud_delete('sales_orders', sid)
    return jsonify({'success': True})


# ==================== 5. 物料管理 ====================
@app.route('/api/materials', methods=['GET'])
def list_materials():
    conn = get_db()
    rows = conn.execute('''
        SELECT m.*, COALESCE(i.quantity, 0) as stock_qty
        FROM materials m
        LEFT JOIN inventory i ON i.mat_id = m.id
        ORDER BY m.id
    ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/materials', methods=['POST'])
def add_material():
    data = request.json
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn = get_db()
        mid = crud_add('materials', data, conn)
        conn.execute('INSERT INTO inventory (mat_id, quantity, updated_at) VALUES (?,0,?)',
                     (mid, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': '物料编号已存在'}), 400
    finally:
        conn.close()
    return jsonify({'success': True})


@app.route('/api/materials/<int:mid>', methods=['PUT'])
def update_material(mid):
    data = request.json
    conn = get_db()
    crud_update('materials', mid, data, conn)
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/materials/<int:mid>', methods=['DELETE'])
def delete_material(mid):
    conn = get_db()
    conn.execute('DELETE FROM inventory WHERE mat_id=?', (mid,))
    conn.execute('DELETE FROM inventory_log WHERE mat_id=?', (mid,))
    conn.execute('DELETE FROM materials WHERE id=?', (mid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ==================== 仓库管理 ====================
@app.route('/api/warehouses', methods=['GET'])
def list_warehouses():
    conn = get_db()
    rows = conn.execute('SELECT * FROM warehouses ORDER BY id').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/warehouses', methods=['POST'])
def add_warehouse():
    data = request.json
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn = get_db()
        crud_add('warehouses', data, conn)
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': '仓库编号已存在'}), 400
    conn.close()
    return jsonify({'success': True})

@app.route('/api/warehouses/<int:wid>', methods=['PUT'])
def update_warehouse(wid):
    data = request.json
    conn = get_db()
    crud_update('warehouses', wid, data, conn)
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/warehouses/<int:wid>', methods=['DELETE'])
def delete_warehouse(wid):
    conn = get_db()
    conn.execute('DELETE FROM storage_locations WHERE warehouse_id=?', (wid,))
    conn.execute('DELETE FROM inventory WHERE warehouse_id=?', (wid,))
    conn.execute('DELETE FROM warehouses WHERE id=?', (wid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ==================== 库位管理 ====================
@app.route('/api/locations', methods=['GET'])
def list_locations():
    warehouse_id = request.args.get('warehouse_id')
    conn = get_db()
    if warehouse_id:
        rows = conn.execute('''
            SELECT l.*, w.name as warehouse_name
            FROM storage_locations l
            LEFT JOIN warehouses w ON w.id = l.warehouse_id
            WHERE l.warehouse_id=? ORDER BY l.location_code
        ''', (warehouse_id,)).fetchall()
    else:
        rows = conn.execute('''
            SELECT l.*, w.name as warehouse_name
            FROM storage_locations l
            LEFT JOIN warehouses w ON w.id = l.warehouse_id
            ORDER BY l.id
        ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/locations', methods=['POST'])
def add_location():
    data = request.json
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn = get_db()
        crud_add('storage_locations', data, conn)
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': '库位编号已存在'}), 400
    conn.close()
    return jsonify({'success': True})

@app.route('/api/locations/<int:lid>', methods=['PUT'])
def update_location(lid):
    data = request.json
    conn = get_db()
    crud_update('storage_locations', lid, data, conn)
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/locations/<int:lid>', methods=['DELETE'])
def delete_location(lid):
    conn = get_db()
    conn.execute('DELETE FROM batch_inventory WHERE location_id=?', (lid,))
    conn.execute('DELETE FROM inventory WHERE location_id=?', (lid,))
    conn.execute('DELETE FROM storage_locations WHERE id=?', (lid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ==================== 批次管理 ====================
@app.route('/api/batches', methods=['GET'])
def list_batches():
    mat_id = request.args.get('mat_id')
    conn = get_db()
    if mat_id:
        rows = conn.execute('''
            SELECT b.*, m.name as mat_name, m.mat_no, s.name as supplier_name
            FROM batches b
            LEFT JOIN materials m ON m.id = b.mat_id
            LEFT JOIN suppliers s ON s.id = b.supplier_id
            WHERE b.mat_id=? AND b.status='active'
            ORDER BY b.production_date ASC
        ''', (mat_id,)).fetchall()
    else:
        rows = conn.execute('''
            SELECT b.*, m.name as mat_name, m.mat_no, s.name as supplier_name
            FROM batches b
            LEFT JOIN materials m ON m.id = b.mat_id
            LEFT JOIN suppliers s ON s.id = b.supplier_id
            WHERE b.status='active'
            ORDER BY b.id DESC
        ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/batches', methods=['POST'])
def add_batch():
    data = request.json
    if not data.get('batch_no'):
        data['batch_no'] = gen_no('BAT')
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['status'] = 'active'
    try:
        conn = get_db()
        bid = crud_add('batches', data, conn)
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': '批次编号已存在'}), 400
    conn.close()
    return jsonify({'success': True, 'id': bid})

@app.route('/api/batches/<int:bid>', methods=['PUT'])
def update_batch(bid):
    data = request.json
    conn = get_db()
    crud_update('batches', bid, data, conn)
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/batches/<int:bid>', methods=['DELETE'])
def delete_batch(bid):
    conn = get_db()
    conn.execute('DELETE FROM batch_inventory WHERE batch_id=?', (bid,))
    conn.execute('DELETE FROM batches WHERE id=?', (bid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ==================== 库存查询（增强版）===================
@app.route('/api/inventory/stock', methods=['GET'])
def get_inventory_stock():
    mat_id = request.args.get('mat_id')
    warehouse_id = request.args.get('warehouse_id')
    conn = get_db()
    
    query = '''
        SELECT i.*, m.name as mat_name, m.mat_no, m.spec, m.unit, m.min_stock, m.max_stock,
               w.name as warehouse_name, l.location_code, l.location_name,
               (i.quantity - i.locked_qty) as available_qty
        FROM inventory i
        JOIN materials m ON m.id = i.mat_id
        LEFT JOIN warehouses w ON w.id = i.warehouse_id
        LEFT JOIN storage_locations l ON l.id = i.location_id
        WHERE 1=1
    '''
    params = []
    if mat_id:
        query += ' AND i.mat_id=?'
        params.append(mat_id)
    if warehouse_id:
        query += ' AND i.warehouse_id=?'
        params.append(warehouse_id)
    query += ' ORDER BY m.mat_no, w.code, l.location_code'
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/inventory/summary', methods=['GET'])
def get_inventory_summary():
    """库存汇总报表"""
    conn = get_db()
    
    # 按物料汇总
    mat_summary = conn.execute('''
        SELECT m.id, m.mat_no, m.name, m.spec, m.unit, m.category, m.min_stock, m.max_stock,
               COALESCE((SELECT SUM(quantity) FROM inventory WHERE mat_id = m.id), 0) as total_qty,
               COALESCE((SELECT SUM(locked_qty) FROM inventory WHERE mat_id = m.id), 0) as total_locked,
               (COALESCE((SELECT SUM(quantity) FROM inventory WHERE mat_id = m.id), 0) - COALESCE((SELECT SUM(locked_qty) FROM inventory WHERE mat_id = m.id), 0)) as available_qty
        FROM materials m
        ORDER BY m.mat_no
    ''').fetchall()
    
    # 按仓库汇总
    wh_summary = conn.execute('''
        SELECT w.id, w.code, w.name, w.manager,
               COALESCE((SELECT SUM(quantity) FROM inventory WHERE warehouse_id = w.id), 0) as total_qty,
               (SELECT COUNT(DISTINCT mat_id) FROM inventory WHERE warehouse_id = w.id) as mat_count
        FROM warehouses w
        ORDER BY w.code
    ''').fetchall()
    
    # 库存预警 - 简化为只返回低库存预警（因为复杂查询在SQLite中受限）
    alerts = []
    mats = conn.execute('SELECT id, mat_no, name, spec, unit, min_stock, max_stock FROM materials WHERE min_stock > 0').fetchall()
    for m in mats:
        qty_row = conn.execute('SELECT COALESCE(SUM(quantity), 0) as qty FROM inventory WHERE mat_id = ?', (m['id'],)).fetchone()
        qty = qty_row['qty'] if qty_row else 0
        if qty < m['min_stock']:
            alerts.append({
                'mat_no': m['mat_no'],
                'name': m['name'],
                'spec': m['spec'],
                'unit': m['unit'],
                'min_stock': m['min_stock'],
                'max_stock': m['max_stock'],
                'current_qty': qty,
                'alert_type': 'low'
            })
    
    conn.close()
    return jsonify({
        'materials': [dict(r) for r in mat_summary],
        'warehouses': [dict(r) for r in wh_summary],
        'alerts': alerts
    })


# ==================== 智能入库 ====================
@app.route('/api/inventory/smart-in', methods=['POST'])
def smart_inventory_in():
    """
    智能入库：支持批次、库位选择
    自动创建批次（FIFO优先）
    """
    data = request.json
    mat_id = data.get('mat_id')
    quantity = float(data.get('quantity', 0))
    warehouse_id = data.get('warehouse_id')
    location_id = data.get('location_id')
    supplier_id = data.get('supplier_id')
    batch_id = data.get('batch_id')
    unit_price = float(data.get('unit_price', 0))
    production_date = data.get('production_date')
    expire_date = data.get('expire_date')
    remark = data.get('remark', '')
    operator = data.get('operator', DEFAULT_USER)
    
    if not mat_id or quantity <= 0:
        return jsonify({'error': '物料和数量不能为空'}), 400
    
    conn = get_db()
    conn.execute('BEGIN')
    
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 如果指定了批次，使用指定批次
        if batch_id:
            # 更新批次库存
            conn.execute('''
                UPDATE batches SET quantity = quantity + ? WHERE id=?
            ''', (quantity, batch_id))
            
            # 更新或创建批次库存记录
            existing = conn.execute('SELECT id FROM batch_inventory WHERE batch_id=? AND location_id=?',
                                   (batch_id, location_id)).fetchone()
            if existing:
                conn.execute('UPDATE batch_inventory SET quantity=quantity+?, updated_at=? WHERE id=?',
                            (quantity, now, existing['id']))
            else:
                conn.execute('INSERT INTO batch_inventory (batch_id, location_id, quantity, updated_at) VALUES (?,?,?,?)',
                            (batch_id, location_id, quantity, now))
        else:
            # 自动创建新批次
            batch_no = gen_no('BAT')
            conn.execute('''
                INSERT INTO batches (batch_no, mat_id, supplier_id, production_date, expire_date, quantity, status, created_at)
                VALUES (?,?,?,?,?,?,?,?)
            ''', (batch_no, mat_id, supplier_id, production_date, expire_date, quantity, 'active', now))
            batch_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            
            # 创建批次库存记录
            if location_id:
                conn.execute('INSERT INTO batch_inventory (batch_id, location_id, quantity, updated_at) VALUES (?,?,?,?)',
                            (batch_id, location_id, quantity, now))
        
        # 更新主库存
        existing_inv = conn.execute('SELECT id FROM inventory WHERE mat_id=? AND warehouse_id=? AND location_id=?',
                                   (mat_id, warehouse_id, location_id)).fetchone()
        if existing_inv:
            conn.execute('''
                UPDATE inventory SET quantity=quantity+?, updated_at=? WHERE id=?
            ''', (quantity, now, existing_inv['id']))
        else:
            conn.execute('''
                INSERT INTO inventory (mat_id, warehouse_id, location_id, quantity, updated_at)
                VALUES (?,?,?,?,?)
            ''', (mat_id, warehouse_id, location_id, quantity, now))
        
        # 记录出入库日志
        conn.execute('''
            INSERT INTO inventory_log (mat_id, batch_id, warehouse_id, location_id, type, quantity, unit_price, total_amount, operator, remark, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ''', (mat_id, batch_id, warehouse_id, location_id, 'in', quantity, unit_price, quantity * unit_price, operator, remark, now))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'batch_id': batch_id})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500


# ==================== 智能出库 ====================
@app.route('/api/inventory/smart-out', methods=['POST'])
def smart_inventory_out():
    """
    智能出库：支持FIFO自动选择批次
    库存不足检查
    """
    data = request.json
    mat_id = data.get('mat_id')
    quantity = float(data.get('quantity', 0))
    warehouse_id = data.get('warehouse_id')
    location_id = data.get('location_id')
    batch_id = data.get('batch_id')
    ref_type = data.get('ref_type')
    ref_id = data.get('ref_id')
    remark = data.get('remark', '')
    operator = data.get('operator', DEFAULT_USER)
    
    if not mat_id or quantity <= 0:
        return jsonify({'error': '物料和数量不能为空'}), 400
    
    conn = get_db()
    conn.execute('BEGIN')
    
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 检查库存
        if warehouse_id:
            row = conn.execute('''
                SELECT quantity, locked_qty FROM inventory 
                WHERE mat_id=? AND warehouse_id=? AND (location_id=? OR ?=0)
            ''', (mat_id, warehouse_id, location_id, 1 if location_id else 0)).fetchone()
        else:
            row = conn.execute('''
                SELECT COALESCE(SUM(quantity), 0) as quantity, COALESCE(SUM(locked_qty), 0) as locked_qty
                FROM inventory WHERE mat_id=?
            ''', (mat_id,)).fetchone()
        
        available = float(row['quantity']) - float(row['locked_qty'])
        if available < quantity:
            conn.rollback()
            conn.close()
            return jsonify({'error': f'库存不足，当前可用: {available}'}), 400
        
        # FIFO出库
        if batch_id:
            # 指定批次出库
            batch_row = conn.execute('SELECT quantity FROM batches WHERE id=?', (batch_id,)).fetchone()
            if not batch_row or float(batch_row['quantity']) < quantity:
                conn.rollback()
                conn.close()
                return jsonify({'error': '批次库存不足'}), 400
            
            conn.execute('UPDATE batches SET quantity=quantity-? WHERE id=?', (quantity, batch_id))
            
            # 更新批次库存
            batch_inv = conn.execute('SELECT id, quantity FROM batch_inventory WHERE batch_id=? AND (location_id=? OR ?=1)',
                                    (batch_id, location_id, 1 if location_id else 0)).fetchone()
            if batch_inv:
                conn.execute('UPDATE batch_inventory SET quantity=quantity-?, updated_at=? WHERE id=?',
                            (quantity, now, batch_inv['id']))
        else:
            # 自动FIFO：按生产日期从早到晚出库
            remaining = quantity
            batches = conn.execute('''
                SELECT b.id, b.quantity, bi.id as bi_id, bi.quantity as bi_qty
                FROM batches b
                JOIN batch_inventory bi ON bi.batch_id = b.id
                WHERE b.mat_id=? AND b.status='active' AND b.quantity > 0
                ORDER BY b.production_date ASC, b.created_at ASC
            ''', (mat_id,)).fetchall()
            
            for b in batches:
                if remaining <= 0:
                    break
                deduct = min(remaining, float(b['quantity']))
                conn.execute('UPDATE batches SET quantity=quantity-? WHERE id=?', (deduct, b['id']))
                conn.execute('UPDATE batch_inventory SET quantity=quantity-?, updated_at=? WHERE id=?',
                            (deduct, now, b['bi_id']))
                remaining -= deduct
            
            if remaining > 0:
                conn.rollback()
                conn.close()
                return jsonify({'error': '批次分配异常'}), 400
        
        # 更新主库存
        if warehouse_id:
            conn.execute('''
                UPDATE inventory SET quantity=quantity-?, updated_at=? 
                WHERE mat_id=? AND warehouse_id=? AND (location_id=? OR ?=0)
            ''', (quantity, now, mat_id, warehouse_id, location_id, 1 if location_id else 0))
        
        # 记录出入库日志
        conn.execute('''
            INSERT INTO inventory_log (mat_id, batch_id, warehouse_id, location_id, type, quantity, ref_type, ref_id, operator, remark, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ''', (mat_id, batch_id, warehouse_id, location_id, 'out', quantity, ref_type, ref_id, operator, remark, now))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500


# ==================== 库存台账 ====================
@app.route('/api/inventory/ledger', methods=['GET'])
def inventory_ledger():
    """库存台账：出入库明细"""
    mat_id = request.args.get('mat_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    log_type = request.args.get('type')
    
    conn = get_db()
    query = '''
        SELECT l.*, m.name as mat_name, m.mat_no, m.unit,
               w.name as warehouse_name, loc.location_code,
               b.batch_no, s.name as supplier_name
        FROM inventory_log l
        JOIN materials m ON m.id = l.mat_id
        LEFT JOIN warehouses w ON w.id = l.warehouse_id
        LEFT JOIN storage_locations loc ON loc.id = l.location_id
        LEFT JOIN batches b ON b.id = l.batch_id
        LEFT JOIN suppliers s ON s.id = b.supplier_id
        WHERE 1=1
    '''
    params = []
    
    if mat_id:
        query += ' AND l.mat_id=?'
        params.append(mat_id)
    if start_date:
        query += ' AND l.created_at >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND l.created_at <= ?'
        params.append(end_date + ' 23:59:59')
    if log_type:
        query += ' AND l.type=?'
        params.append(log_type)
    
    query += ' ORDER BY l.id DESC LIMIT 500'
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ==================== 库存统计报表 ====================
@app.route('/api/inventory/report', methods=['GET'])
def inventory_report():
    """出入库统计报表"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = get_db()
    
    # 按日期统计
    daily_stats = conn.execute('''
        SELECT DATE(created_at) as stat_date,
               SUM(CASE WHEN type='in' THEN quantity ELSE 0 END) as in_qty,
               SUM(CASE WHEN type='out' THEN quantity ELSE 0 END) as out_qty,
               COUNT(*) as op_count
        FROM inventory_log
        WHERE created_at BETWEEN ? AND ?
        GROUP BY DATE(created_at)
        ORDER BY stat_date DESC
    ''', (start_date or '2026-01-01', end_date or '2099-12-31')).fetchall()
    
    # 按物料统计
    mat_stats = conn.execute('''
        SELECT m.mat_no, m.name, m.unit,
               SUM(CASE WHEN l.type='in' THEN l.quantity ELSE 0 END) as total_in,
               SUM(CASE WHEN l.type='out' THEN l.quantity ELSE 0 END) as total_out,
               COUNT(*) as op_count
        FROM inventory_log l
        JOIN materials m ON m.id = l.mat_id
        WHERE l.created_at BETWEEN ? AND ?
        GROUP BY m.id
        ORDER BY total_in DESC
    ''', (start_date or '2026-01-01', end_date or '2099-12-31')).fetchall()
    
    # 汇总
    total = conn.execute('''
        SELECT 
            SUM(CASE WHEN type='in' THEN quantity ELSE 0 END) as total_in,
            SUM(CASE WHEN type='out' THEN quantity ELSE 0 END) as total_out,
            SUM(CASE WHEN type='in' THEN total_amount ELSE 0 END) as total_in_amount,
            COUNT(*) as total_ops
        FROM inventory_log
        WHERE created_at BETWEEN ? AND ?
    ''', (start_date or '2026-01-01', end_date or '2099-12-31')).fetchone()
    
    conn.close()
    return jsonify({
        'daily': [dict(r) for r in daily_stats],
        'byMaterial': [dict(r) for r in mat_stats],
        'summary': dict(total) if total else {'total_in': 0, 'total_out': 0, 'total_in_amount': 0, 'total_ops': 0}
    })


# ==================== 库存预警（智能）====================
@app.route('/api/inventory/smart-alerts', methods=['GET'])
def smart_alerts():
    """智能库存预警"""
    conn = get_db()
    today = datetime.now().strftime('%Y-%m-%d')
    stagnant_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    # 低库存预警
    low_stock = conn.execute('''
        SELECT m.mat_no, m.name, m.spec, m.unit, m.min_stock, m.max_stock,
               COALESCE((SELECT SUM(quantity) FROM inventory WHERE mat_id = m.id), 0) as current_qty,
               ROUND(COALESCE((SELECT SUM(quantity) FROM inventory WHERE mat_id = m.id), 0) / NULLIF(m.min_stock, 0) * 100, 1) as stock_rate,
               'low' as alert_type
        FROM materials m
        WHERE m.min_stock > 0 AND COALESCE((SELECT SUM(quantity) FROM inventory WHERE mat_id = m.id), 0) < m.min_stock
        ORDER BY (COALESCE((SELECT SUM(quantity) FROM inventory WHERE mat_id = m.id), 0) / NULLIF(m.min_stock, 0)) ASC
    ''').fetchall()
    
    # 临近过期预警（30天内）
    near_expire = conn.execute('''
        SELECT b.batch_no, m.mat_no, m.name, b.expire_date,
               julianday(b.expire_date) - julianday(?) as days_left,
               b.quantity
        FROM batches b
        JOIN materials m ON m.id = b.mat_id
        WHERE b.expire_date IS NOT NULL 
          AND b.expire_date != ''
          AND b.expire_date != 'None'
          AND julianday(b.expire_date) - julianday(?) <= 30
          AND b.quantity > 0
        ORDER BY days_left ASC
    ''', (today, today)).fetchall()
    
    # 呆滞物料（90天无进出）- 使用Python循环处理
    stagnant = []
    mats = conn.execute('SELECT id, mat_no, name, unit FROM materials').fetchall()
    for m in mats:
        qty_row = conn.execute('SELECT COALESCE(SUM(quantity), 0) as qty FROM inventory WHERE mat_id = ?', (m['id'],)).fetchone()
        last_row = conn.execute('SELECT MAX(created_at) as last_op FROM inventory_log WHERE mat_id = ?', (m['id'],)).fetchone()
        qty = qty_row['qty'] if qty_row else 0
        last_op = last_row['last_op'] if last_row else None
        if qty > 0 and (last_op is None or last_op < stagnant_date + ' 00:00:00'):
            stagnant.append({
                'mat_no': m['mat_no'],
                'name': m['name'],
                'unit': m['unit'],
                'qty': qty,
                'last_op': last_op
            })
    stagnant.sort(key=lambda x: x['qty'], reverse=True)
    
    conn.close()
    return jsonify({
        'lowStock': [dict(r) for r in low_stock],
        'nearExpire': [dict(r) for r in near_expire],
        'stagnant': [dict(r) for r in stagnant]
    })


# ==================== 6. 库存出入库（兼容旧API）====================
@app.route('/api/inventory/in', methods=['POST'])
def inventory_in():
    data = request.json
    conn = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 兼容旧API，自动创建批次
    batch_no = gen_no('BAT')
    conn.execute('''
        INSERT INTO batches (batch_no, mat_id, quantity, status, created_at)
        VALUES (?,?,?,?,?)
    ''', (batch_no, data['mat_id'], data['quantity'], 'active', now))
    batch_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    
    conn.execute('BEGIN')
    conn.execute('UPDATE inventory SET quantity=quantity+?, updated_at=? WHERE mat_id=?',
                 (data['quantity'], now, data['mat_id']))
    conn.execute('INSERT INTO inventory_log (mat_id, batch_id, type, quantity, operator, remark, created_at) VALUES (?,?,?,?,?,?,?)',
                 (data['mat_id'], batch_id, 'in', data['quantity'], DEFAULT_USER,
                  data.get('remark', ''), now))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/inventory/out', methods=['POST'])
def inventory_out():
    data = request.json
    conn = get_db()
    row = conn.execute('SELECT quantity FROM inventory WHERE mat_id=?', (data['mat_id'],)).fetchone()
    if not row or float(row['quantity']) < data['quantity']:
        conn.close()
        return jsonify({'error': '库存不足'}), 400
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute('BEGIN')
    conn.execute('UPDATE inventory SET quantity=quantity-?, updated_at=? WHERE mat_id=?',
                 (data['quantity'], now, data['mat_id']))
    conn.execute('INSERT INTO inventory_log (mat_id, type, quantity, operator, remark, created_at) VALUES (?,?,?,?,?,?)',
                 (data['mat_id'], 'out', data['quantity'], DEFAULT_USER,
                  data.get('remark', ''), now))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/inventory/logs', methods=['GET'])
def inventory_logs():
    conn = get_db()
    rows = conn.execute('''
        SELECT l.*, m.name as mat_name, m.mat_no
        FROM inventory_log l
        JOIN materials m ON m.id = l.mat_id
        ORDER BY l.id DESC LIMIT 200
    ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/inventory/alerts', methods=['GET'])
def inventory_alerts():
    conn = get_db()
    rows = conn.execute('''
        SELECT m.mat_no, m.name, m.min_stock, COALESCE(i.quantity, 0) as stock_qty
        FROM materials m
        LEFT JOIN inventory i ON i.mat_id = m.id
        WHERE COALESCE(i.quantity, 0) < m.min_stock AND m.min_stock > 0
    ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ==================== 7. 运营请购 ====================
@app.route('/api/requisitions', methods=['GET'])
def list_requisitions():
    conn = get_db()
    rows = conn.execute('''
        SELECT r.*, m.name as mat_name, m.mat_no, s.order_no as so_no
        FROM purchase_requisitions r
        LEFT JOIN materials m ON m.id = r.material_id
        LEFT JOIN sales_orders s ON s.id = r.sales_order_id
        ORDER BY r.id DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/requisitions', methods=['POST'])
def add_requisition():
    data = request.json
    data['req_no'] = gen_no('PR')
    data['status'] = 'pending'
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db()
    crud_add('purchase_requisitions', data, conn)
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/requisitions/<int:rid>', methods=['PUT'])
def update_requisition(rid):
    data = request.json
    conn = get_db()
    crud_update('purchase_requisitions', rid, data, conn)
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/requisitions/<int:rid>/approve', methods=['POST'])
def approve_requisition(rid):
    conn = get_db()
    conn.execute("UPDATE purchase_requisitions SET status='approved' WHERE id=?", (rid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/requisitions/<int:rid>', methods=['DELETE'])
def delete_requisition(rid):
    crud_delete('purchase_requisitions', rid)
    return jsonify({'success': True})


# ==================== 8. 供应商管理 ====================
@app.route('/api/suppliers', methods=['GET'])
def list_suppliers():
    return crud_get('suppliers')


@app.route('/api/suppliers', methods=['POST'])
def add_supplier():
    data = request.json
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn = get_db()
        crud_add('suppliers', data, conn)
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': '供应商编号已存在'}), 400
    finally:
        conn.close()
    return jsonify({'success': True})


@app.route('/api/suppliers/<int:sid>', methods=['PUT'])
def update_supplier(sid):
    data = request.json
    conn = get_db()
    crud_update('suppliers', sid, data, conn)
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/suppliers/<int:sid>', methods=['DELETE'])
def delete_supplier(sid):
    crud_delete('suppliers', sid)
    return jsonify({'success': True})


# ==================== 9. 采购订单 ====================
@app.route('/api/purchases', methods=['GET'])
def list_purchases():
    conn = get_db()
    rows = conn.execute('''
        SELECT p.*, s.name as supplier_name, m.name as mat_name, m.mat_no, r.req_no
        FROM purchase_orders p
        LEFT JOIN suppliers s ON s.id = p.supplier_id
        LEFT JOIN materials m ON m.id = p.material_id
        LEFT JOIN purchase_requisitions r ON r.id = p.req_id
        ORDER BY p.id DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/purchases', methods=['POST'])
def add_purchase():
    data = request.json
    data['po_no'] = gen_no('PO')
    data['status'] = 'pending'
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db()
    crud_add('purchase_orders', data, conn)
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/purchases/<int:pid>/arrive', methods=['POST'])
def purchase_arrive(pid):
    conn = get_db()
    conn.execute("UPDATE purchase_orders SET status='arrived' WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/purchases/<int:pid>/stockin', methods=['POST'])
def purchase_stockin(pid):
    conn = get_db()
    po = conn.execute('SELECT * FROM purchase_orders WHERE id=?', (pid,)).fetchone()
    conn.execute('BEGIN')
    conn.execute('UPDATE inventory SET quantity=quantity+?, updated_at=? WHERE mat_id=?',
                 (po['order_qty'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), po['material_id']))
    conn.execute('INSERT INTO inventory_log (mat_id, type, quantity, operator, remark, created_at) VALUES (?,?,?,?,?,?)',
                 (po['material_id'], 'in', po['order_qty'], DEFAULT_USER,
                  '采购入库: ' + po['po_no'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.execute("UPDATE purchase_orders SET status='stocked' WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/purchases/<int:pid>', methods=['DELETE'])
def delete_purchase(pid):
    crud_delete('purchase_orders', pid)
    return jsonify({'success': True})


# ==================== 10. 设备管理 ====================
@app.route('/api/equipment', methods=['GET'])
def list_equipment():
    return crud_get('equipment')


@app.route('/api/equipment', methods=['POST'])
def add_equipment():
    data = request.json
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn = get_db()
        crud_add('equipment', data, conn)
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': '设备编号已存在'}), 400
    finally:
        conn.close()
    return jsonify({'success': True})


@app.route('/api/equipment/<int:eid>', methods=['PUT'])
def update_equipment(eid):
    data = request.json
    conn = get_db()
    crud_update('equipment', eid, data, conn)
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/equipment/<int:eid>', methods=['DELETE'])
def delete_equipment(eid):
    conn = get_db()
    conn.execute('DELETE FROM equipment_repair WHERE eq_id=?', (eid,))
    conn.execute('DELETE FROM equipment WHERE id=?', (eid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/equipment/<int:eid>/repair', methods=['POST'])
def add_repair(eid):
    data = request.json
    conn = get_db()
    conn.execute(
        'INSERT INTO equipment_repair (eq_id, fault_desc, repair_desc, cost, operator, status, created_at) VALUES (?,?,?,?,?,?,?)',
        (eid, data.get('fault_desc', ''), '', data.get('cost', 0),
         DEFAULT_USER, 'pending', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.execute("UPDATE equipment SET status='maintenance' WHERE id=?", (eid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/equipment/<int:eid>/repairs', methods=['GET'])
def list_repairs(eid):
    conn = get_db()
    rows = conn.execute('SELECT * FROM equipment_repair WHERE eq_id=? ORDER BY id DESC', (eid,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/equipment/<int:eid>/repair/done', methods=['POST'])
def finish_repair(eid):
    data = request.json
    conn = get_db()
    conn.execute("UPDATE equipment_repair SET status='done', repair_desc=? WHERE id=?",
                 (data.get('repair_desc', ''), data['repair_id']))
    conn.execute("UPDATE equipment SET status='normal' WHERE id=?", (eid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ==================== 11. 生产工单（改造：关联销售订单）====================
@app.route('/api/production', methods=['GET'])
def list_production():
    status = request.args.get('status', '')
    conn = get_db()
    if status:
        rows = conn.execute('''
            SELECT p.*, s.order_no as so_no
            FROM production_orders p
            LEFT JOIN sales_orders s ON s.id = p.sales_order_id
            WHERE p.status=? ORDER BY p.id DESC
        ''', (status,)).fetchall()
    else:
        rows = conn.execute('''
            SELECT p.*, s.order_no as so_no
            FROM production_orders p
            LEFT JOIN sales_orders s ON s.id = p.sales_order_id
            ORDER BY p.id DESC
        ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/production', methods=['POST'])
def add_production():
    data = request.json
    data['order_no'] = gen_no('WO')
    data['completed_qty'] = 0
    data['created_by'] = DEFAULT_USER
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db()
    crud_add('production_orders', data, conn)
    # 如果关联了销售订单，更新销售订单状态为生产中
    if data.get('sales_order_id'):
        conn.execute("UPDATE sales_orders SET status='producing' WHERE id=?", (data['sales_order_id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/production/<int:oid>', methods=['PUT'])
def update_production(oid):
    data = request.json
    conn = get_db()
    crud_update('production_orders', oid, data, conn)
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/production/<int:oid>/complete', methods=['POST'])
def complete_production(oid):
    data = request.json
    conn = get_db()
    conn.execute('UPDATE production_orders SET completed_qty=?, status=? WHERE id=?',
                 (data.get('completed_qty', 0), 'done', oid))
    # 自动成品入库
    order = conn.execute('SELECT * FROM production_orders WHERE id=?', (oid,)).fetchone()
    if order:
        # 检查成品库存是否存在
        existing = conn.execute('SELECT * FROM finished_products WHERE production_order_id=?', (oid,)).fetchone()
        if existing:
            conn.execute('UPDATE finished_products SET quantity=quantity+?, updated_at=? WHERE id=?',
                         (order['completed_qty'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), existing['id']))
        else:
            conn.execute('''
                INSERT INTO finished_products (product_name, spec, quantity, sales_order_id, production_order_id, location, updated_at)
                VALUES (?,?,?,?,?,?,?)
            ''', (order['product_name'], order.get('product_spec', ''), order['completed_qty'],
                  order['sales_order_id'], oid, '', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        # 更新生产工单状态为已入库
        conn.execute("UPDATE production_orders SET status='stocked' WHERE id=?", (oid,))
        # 更新销售订单状态
        if order['sales_order_id']:
            conn.execute("UPDATE sales_orders SET status='stocked' WHERE id=?", (order['sales_order_id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/production/<int:oid>', methods=['DELETE'])
def delete_production(oid):
    crud_delete('production_orders', oid)
    return jsonify({'success': True})


# ==================== 12. 成品库存 ====================
@app.route('/api/finished', methods=['GET'])
def list_finished():
    conn = get_db()
    rows = conn.execute('''
        SELECT f.*, s.order_no as so_no
        FROM finished_products f
        LEFT JOIN sales_orders s ON s.id = f.sales_order_id
        ORDER BY f.id DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/finished/<int:fid>/ship', methods=['POST'])
def ship_finished(fid):
    data = request.json
    conn = get_db()
    f = conn.execute('SELECT * FROM finished_products WHERE id=?', (fid,)).fetchone()
    if not f or f['quantity'] < data['ship_qty']:
        conn.close()
        return jsonify({'error': '成品库存不足'}), 400
    conn.execute('UPDATE finished_products SET quantity=quantity-?, updated_at=? WHERE id=?',
                 (data['ship_qty'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), fid))
    # 创建发货单
    conn.execute('''
        INSERT INTO shipments (ship_no, sales_order_id, shipped_qty, carrier, tracking_no, status, shipped_at, remark, created_at)
        VALUES (?,?,?,?,?,?,?,?,?)
    ''', (gen_no('SH'), f['sales_order_id'], data['ship_qty'],
          data.get('carrier', ''), data.get('tracking_no', ''),
          'shipped', datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
          data.get('remark', ''), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    # 更新销售订单状态
    if f['sales_order_id']:
        conn.execute("UPDATE sales_orders SET status='shipped' WHERE id=?", (f['sales_order_id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ==================== 13. 发货管理 ====================
@app.route('/api/shipments', methods=['GET'])
def list_shipments():
    conn = get_db()
    rows = conn.execute('''
        SELECT s.*, so.order_no as so_no, so.product_name
        FROM shipments s
        LEFT JOIN sales_orders so ON so.id = s.sales_order_id
        ORDER BY s.id DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/shipments/<int:shid>/receive', methods=['POST'])
def receive_shipment(shid):
    conn = get_db()
    sh = conn.execute('SELECT * FROM shipments WHERE id=?', (shid,)).fetchone()
    conn.execute("UPDATE shipments SET status='received' WHERE id=?", (shid,))
    if sh['sales_order_id']:
        conn.execute("UPDATE sales_orders SET status='done' WHERE id=?", (sh['sales_order_id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ==================== 14. 质量管理 ====================
@app.route('/api/quality', methods=['GET'])
def list_quality():
    conn = get_db()
    rows = conn.execute('''
        SELECT q.*, p.order_no, p.product_name
        FROM quality_checks q
        LEFT JOIN production_orders p ON p.id = q.order_id
        ORDER BY q.id DESC LIMIT 200
    ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/quality', methods=['POST'])
def add_quality():
    data = request.json
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db()
    crud_add('quality_checks', data, conn)
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/quality/<int:qid>', methods=['DELETE'])
def delete_quality(qid):
    crud_delete('quality_checks', qid)
    return jsonify({'success': True})


# ==================== 15. 考勤 ====================
@app.route('/api/attendance/checkin', methods=['POST'])
def check_in():
    data = request.json
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db()
    existing = conn.execute('SELECT id FROM attendance WHERE emp_id=? AND work_date=?',
                          (data['emp_id'], today)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': '今日已签到'}), 400
    conn.execute('INSERT INTO attendance (emp_id, check_in, work_date) VALUES (?,?,?)',
                 (data['emp_id'], datetime.now().strftime('%H:%M:%S'), today))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/attendance/checkout', methods=['POST'])
def check_out():
    data = request.json
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db()
    conn.execute('UPDATE attendance SET check_out=? WHERE emp_id=? AND work_date=?',
                 (datetime.now().strftime('%H:%M:%S'), data['emp_id'], today))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/attendance', methods=['GET'])
def list_attendance():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    conn = get_db()
    rows = conn.execute('''
        SELECT a.*, e.emp_no, e.name
        FROM attendance a
        JOIN employees e ON e.id = a.emp_id
        WHERE a.work_date = ?
        ORDER BY a.id
    ''', (date,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ==================== 看板（全链路）====================
@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    conn = get_db()

    # 销售订单统计
    so_total = conn.execute('SELECT COUNT(*) as c FROM sales_orders').fetchone()['c']
    so_pending = conn.execute("SELECT COUNT(*) as c FROM sales_orders WHERE status='pending'").fetchone()['c']
    so_producing = conn.execute("SELECT COUNT(*) as c FROM sales_orders WHERE status='producing'").fetchone()['c']
    so_shipped = conn.execute("SELECT COUNT(*) as c FROM sales_orders WHERE status='shipped'").fetchone()['c']

    # 请购统计
    req_pending = conn.execute("SELECT COUNT(*) as c FROM purchase_requisitions WHERE status='pending'").fetchone()['c']

    # 采购统计
    po_pending = conn.execute("SELECT COUNT(*) as c FROM purchase_orders WHERE status='pending'").fetchone()['c']
    po_arrived = conn.execute("SELECT COUNT(*) as c FROM purchase_orders WHERE status='arrived'").fetchone()['c']

    # 生产统计
    total_orders = conn.execute('SELECT COUNT(*) as c FROM production_orders').fetchone()['c']
    pending_orders = conn.execute("SELECT COUNT(*) as c FROM production_orders WHERE status='pending'").fetchone()['c']
    ongoing_orders = conn.execute("SELECT COUNT(*) as c FROM production_orders WHERE status='ongoing'").fetchone()['c']
    done_orders = conn.execute("SELECT COUNT(*) as c FROM production_orders WHERE status='done'").fetchone()['c']

    # 设备统计
    total_equipment = conn.execute('SELECT COUNT(*) as c FROM equipment').fetchone()['c']
    normal_eq = conn.execute("SELECT COUNT(*) as c FROM equipment WHERE status='normal'").fetchone()['c']
    maintenance_eq = conn.execute("SELECT COUNT(*) as c FROM equipment WHERE status='maintenance'").fetchone()['c']

    # 库存预警
    alerts = conn.execute('''
        SELECT m.mat_no, m.name, m.min_stock, COALESCE(i.quantity, 0) as stock_qty
        FROM materials m
        LEFT JOIN inventory i ON i.mat_id = m.id
        WHERE COALESCE(i.quantity, 0) < m.min_stock AND m.min_stock > 0
    ''').fetchall()

    conn.close()
    return jsonify({
        'sales': {'total': so_total, 'pending': so_pending, 'producing': so_producing, 'shipped': so_shipped},
        'requisitions': {'pending': req_pending},
        'purchases': {'pending': po_pending, 'arrived': po_arrived},
        'production': {'total': total_orders, 'pending': pending_orders, 'ongoing': ongoing_orders, 'done': done_orders},
        'equipment': {'total': total_equipment, 'normal': normal_eq, 'maintenance': maintenance_eq},
        'inventory_alerts': [dict(r) for r in alerts]
    })


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # 禁用外键约束以避免问题
    conn.execute('PRAGMA foreign_keys = OFF')
    return conn


def init_db():
    """初始化数据库"""
    os.makedirs(os.path.join(BASE_DIR, 'db'), exist_ok=True)
    conn = get_db()
    
    # 创建表（不使用外键约束，避免问题）
    conn.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mat_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            unit TEXT DEFAULT '件',
            spec TEXT,
            min_stock REAL DEFAULT 0,
            max_stock REAL DEFAULT 0,
            location TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE,
            address TEXT,
            manager TEXT,
            tel TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse_id INTEGER,
            location_code TEXT UNIQUE NOT NULL,
            location_name TEXT,
            zone TEXT,
            capacity REAL DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            name TEXT NOT NULL,
            contact TEXT,
            tel TEXT,
            address TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            name TEXT NOT NULL,
            contact TEXT,
            tel TEXT,
            address TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_no TEXT UNIQUE NOT NULL,
            mat_id INTEGER,
            supplier_id INTEGER,
            production_date TEXT,
            expire_date TEXT,
            quantity REAL DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS batch_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER,
            location_id INTEGER,
            quantity REAL DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS inventory_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            mat_id INTEGER,
            batch_id INTEGER,
            warehouse_id INTEGER,
            location_id INTEGER,
            quantity REAL,
            unit_price REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            ref_type TEXT,
            ref_id INTEGER,
            operator TEXT,
            remark TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    
    # 添加默认数据
    mat_count = conn.execute('SELECT COUNT(*) as c FROM materials').fetchone()['c']
    if mat_count == 0:
        # 默认物料
        conn.execute("INSERT INTO materials (mat_no, name, category, unit, spec, min_stock, max_stock) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    ('MAT001', '螺丝 M8x30', '紧固件', '件', 'GB/T 70.1', 100, 1000))
        conn.execute("INSERT INTO materials (mat_no, name, category, unit, spec, min_stock, max_stock) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    ('MAT002', '轴承 6205', '轴承', '个', 'GB/T 276', 50, 500))
        conn.execute("INSERT INTO materials (mat_no, name, category, unit, spec, min_stock, max_stock) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    ('MAT003', '润滑油 5L', '润滑剂', '桶', '美孚DTE22', 20, 200))
        
        # 默认仓库
        conn.execute("INSERT INTO warehouses (name, code, address, manager) VALUES (?, ?, ?, ?)",
                    ('原材料仓库', 'WH01', '厂区A栋1楼', '张三'))
        conn.execute("INSERT INTO warehouses (name, code, address, manager) VALUES (?, ?, ?, ?)",
                    ('成品仓库', 'WH02', '厂区B栋2楼', '李四'))
        
        # 默认库位
        conn.execute("INSERT INTO locations (warehouse_id, location_code, location_name, zone) VALUES (?, ?, ?, ?)",
                    (1, 'A01-01', 'A区01排01位', 'A区'))
        conn.execute("INSERT INTO locations (warehouse_id, location_code, location_name, zone) VALUES (?, ?, ?, ?)",
                    (1, 'A01-02', 'A区01排02位', 'A区'))
        conn.execute("INSERT INTO locations (warehouse_id, location_code, location_name, zone) VALUES (?, ?, ?, ?)",
                    (1, 'B02-01', 'B区02排01位', 'B区'))
        conn.execute("INSERT INTO locations (warehouse_id, location_code, location_name, zone) VALUES (?, ?, ?, ?)",
                    (2, 'C01-01', '成品C区01位', 'C区'))
        
        # 默认供应商
        conn.execute("INSERT INTO suppliers (code, name, contact, tel) VALUES (?, ?, ?, ?)",
                    ('SUP001', '五金配件供应商', '王五', '13800138001'))
        
        conn.commit()
    
    conn.close()


# 启动时初始化数据库
init_db()


if __name__ == '__main__':
    print('=' * 50)
    print('  物料出入库智能化管理系统 v2.0')
    print('  访问地址: http://localhost:5000')
    print('  永久免费使用，无需登录')
    print('=' * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
