import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'factory_erp.db')

# 删除旧库，全新重建
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# ========== 1. 用户表（系统用户）==========
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'worker',
    phone TEXT,
    created_at TEXT NOT NULL
)
''')

# ========== 2. 员工表（加 department 字段）==========
c.execute('''
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_no TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    position TEXT,
    team TEXT,
    phone TEXT,
    department TEXT DEFAULT '',
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL
)
''')

# ========== 3. 客户档案 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_no TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    contact TEXT,
    phone TEXT,
    address TEXT,
    created_at TEXT NOT NULL
)
''')

# ========== 4. 销售订单 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS sales_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    spec TEXT,
    quantity INTEGER NOT NULL,
    unit_price REAL DEFAULT 0,
    total_amount REAL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    delivery_date TEXT,
    remark TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
)
''')

# ========== 5. 物料表 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mat_no TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    spec TEXT,
    unit TEXT,
    category TEXT,
    min_stock REAL DEFAULT 0,
    max_stock REAL,
    created_at TEXT NOT NULL
)
''')

# ========== 6. 仓库表 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS warehouses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    address TEXT,
    manager TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL
)
''')

# ========== 7. 库位表 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS storage_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id INTEGER NOT NULL,
    location_code TEXT NOT NULL,
    location_name TEXT,
    zone TEXT,
    capacity REAL DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
)
''')

# ========== 8. 批次表 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_no TEXT UNIQUE NOT NULL,
    mat_id INTEGER NOT NULL,
    supplier_id INTEGER,
    production_date TEXT,
    expire_date TEXT,
    quantity REAL DEFAULT 0,
    locked_qty REAL DEFAULT 0,
    status TEXT DEFAULT 'active',
    remark TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (mat_id) REFERENCES materials(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
)
''')

# ========== 9. 批次库存表 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS batch_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    location_id INTEGER,
    quantity REAL DEFAULT 0,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (batch_id) REFERENCES batches(id),
    FOREIGN KEY (location_id) REFERENCES storage_locations(id)
)
''')

# ========== 10. 库存（增强版）==========
c.execute('''
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mat_id INTEGER NOT NULL,
    warehouse_id INTEGER,
    location_id INTEGER,
    quantity REAL DEFAULT 0,
    locked_qty REAL DEFAULT 0,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (mat_id) REFERENCES materials(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (location_id) REFERENCES storage_locations(id)
)
''')

# ========== 11. 库存出入库记录（增强版）==========
c.execute('''
CREATE TABLE IF NOT EXISTS inventory_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mat_id INTEGER NOT NULL,
    batch_id INTEGER,
    warehouse_id INTEGER,
    location_id INTEGER,
    type TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit_price REAL DEFAULT 0,
    total_amount REAL DEFAULT 0,
    ref_type TEXT,
    ref_id INTEGER,
    operator TEXT NOT NULL,
    remark TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (mat_id) REFERENCES materials(id),
    FOREIGN KEY (batch_id) REFERENCES batches(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (location_id) REFERENCES storage_locations(id)
)
''')

# ========== 8. 运营请购单 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS purchase_requisitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    req_no TEXT UNIQUE NOT NULL,
    sales_order_id INTEGER,
    material_id INTEGER NOT NULL,
    req_qty REAL NOT NULL,
    applicant TEXT DEFAULT '运营部',
    status TEXT DEFAULT 'pending',
    remark TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id),
    FOREIGN KEY (material_id) REFERENCES materials(id)
)
''')

# ========== 9. 供应商档案 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    contact TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    created_at TEXT NOT NULL
)
''')

# ========== 10. 采购订单 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS purchase_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    po_no TEXT UNIQUE NOT NULL,
    supplier_id INTEGER NOT NULL,
    req_id INTEGER,
    material_id INTEGER NOT NULL,
    order_qty REAL NOT NULL,
    unit_price REAL DEFAULT 0,
    total_amount REAL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    remark TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (req_id) REFERENCES purchase_requisitions(id),
    FOREIGN KEY (material_id) REFERENCES materials(id)
)
''')

# ========== 11. 设备表 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eq_no TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    model TEXT,
    location TEXT,
    status TEXT DEFAULT 'normal',
    created_at TEXT NOT NULL
)
''')

# ========== 12. 设备维修记录 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS equipment_repair (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eq_id INTEGER NOT NULL,
    fault_desc TEXT,
    repair_desc TEXT,
    cost REAL,
    operator TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TEXT NOT NULL,
    FOREIGN KEY (eq_id) REFERENCES equipment(id)
)
''')

# ========== 13. 生产工单（改造：加 sales_order_id, product_spec）==========
c.execute('''
CREATE TABLE IF NOT EXISTS production_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT UNIQUE NOT NULL,
    sales_order_id INTEGER,
    product_name TEXT NOT NULL,
    product_spec TEXT,
    quantity INTEGER NOT NULL,
    completed_qty INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    assignee TEXT,
    start_date TEXT,
    end_date TEXT,
    remark TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id)
)
''')

# ========== 14. 成品库存 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS finished_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    spec TEXT,
    quantity REAL DEFAULT 0,
    sales_order_id INTEGER,
    production_order_id INTEGER,
    location TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id),
    FOREIGN KEY (production_order_id) REFERENCES production_orders(id)
)
''')

# ========== 15. 质检记录 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS quality_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    check_type TEXT,
    result TEXT,
    checker TEXT NOT NULL,
    remark TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES production_orders(id)
)
''')

# ========== 16. 发货单 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS shipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ship_no TEXT UNIQUE NOT NULL,
    sales_order_id INTEGER NOT NULL,
    shipped_qty INTEGER NOT NULL,
    carrier TEXT,
    tracking_no TEXT,
    status TEXT DEFAULT 'pending',
    shipped_at TEXT,
    remark TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id)
)
''')

# ========== 17. 考勤 ==========
c.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id INTEGER NOT NULL,
    check_in TEXT,
    check_out TEXT,
    work_date TEXT NOT NULL,
    FOREIGN KEY (emp_id) REFERENCES employees(id)
)
''')

# ========== 默认数据 ==========

# 默认管理员
import hashlib
c.execute(
    'INSERT INTO users (username, password, name, role, created_at) VALUES (?,?,?,?,?)',
    ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), '管理员', 'admin', '2026-01-01 00:00:00')
)

# 示例客户
c.execute(
    "INSERT INTO customers (customer_no, name, contact, phone, created_at) VALUES ('C001', '示例客户A', '张经理', '13800000000', '2026-01-01 00:00:00')"
)

# 示例供应商
c.execute(
    "INSERT INTO suppliers (code, name, contact, phone, email, address, created_at) VALUES ('S001', '示例供应商B', '李经理', '13900000000', 'li@example.com', '北京市朝阳区', '2026-01-01 00:00:00')"
)

# 示例物料
c.execute(
    "INSERT INTO materials (mat_no, name, spec, unit, category, min_stock, created_at) VALUES ('M001', '示例原料', '标准', 'kg', '原材料', 10, '2026-01-01 00:00:00')"
)
c.execute(
    "INSERT INTO materials (mat_no, name, spec, unit, category, min_stock, created_at) VALUES ('M002', '包装材料', '标准', '个', '包材', 50, '2026-01-01 00:00:00')"
)
c.execute(
    "INSERT INTO materials (mat_no, name, spec, unit, category, min_stock, created_at) VALUES ('M003', '电子元器件', '常规', 'pcs', '电子件', 100, '2026-01-01 00:00:00')"
)

# 默认仓库
c.execute(
    "INSERT INTO warehouses (code, name, address, manager, status, created_at) VALUES ('WH01', '主仓库', '工厂A区', '仓管员A', 'active', '2026-01-01 00:00:00')"
)
c.execute(
    "INSERT INTO warehouses (code, name, address, manager, status, created_at) VALUES ('WH02', '辅料仓库', '工厂B区', '仓管员B', 'active', '2026-01-01 00:00:00')"
)

# 库位数据
c.execute(
    "INSERT INTO storage_locations (warehouse_id, location_code, location_name, zone, capacity, status, created_at) VALUES (1, 'A-01-01', 'A区1号货架1层', 'A区', 1000, 'active', '2026-01-01 00:00:00')"
)
c.execute(
    "INSERT INTO storage_locations (warehouse_id, location_code, location_name, zone, capacity, status, created_at) VALUES (1, 'A-01-02', 'A区1号货架2层', 'A区', 1000, 'active', '2026-01-01 00:00:00')"
)
c.execute(
    "INSERT INTO storage_locations (warehouse_id, location_code, location_name, zone, capacity, status, created_at) VALUES (1, 'A-02-01', 'A区2号货架1层', 'A区', 800, 'active', '2026-01-01 00:00:00')"
)
c.execute(
    "INSERT INTO storage_locations (warehouse_id, location_code, location_name, zone, capacity, status, created_at) VALUES (2, 'B-01-01', 'B区1号货架', 'B区', 500, 'active', '2026-01-01 00:00:00')"
)

# 库存数据
c.execute(
    'INSERT INTO inventory (mat_id, warehouse_id, location_id, quantity, updated_at) VALUES (1, 1, 1, 100, ?)',
    ('2026-01-01 00:00:00',)
)
c.execute(
    'INSERT INTO inventory (mat_id, warehouse_id, location_id, quantity, updated_at) VALUES (2, 2, 4, 200, ?)',
    ('2026-01-01 00:00:00',)
)
c.execute(
    'INSERT INTO inventory (mat_id, warehouse_id, location_id, quantity, updated_at) VALUES (3, 1, 2, 50, ?)',
    ('2026-01-01 00:00:00',)
)

# 示例批次
c.execute(
    "INSERT INTO batches (batch_no, mat_id, supplier_id, production_date, expire_date, quantity, status, created_at) VALUES ('B20260101001', 1, 1, '2026-01-01', '2027-01-01', 100, 'active', '2026-01-01 00:00:00')"
)
c.execute(
    "INSERT INTO batch_inventory (batch_id, location_id, quantity, updated_at) VALUES (1, 1, 100, '2026-01-01 00:00:00')"
)

conn.commit()
conn.close()
print('=' * 50)
print('  数据库初始化完成！')
print('=' * 50)
print('  表结构：')
print('    - 仓库管理: warehouses, storage_locations')
print('    - 物料管理: materials, inventory')
print('    - 批次管理: batches, batch_inventory')
print('    - 出入库: inventory_log')
print('    - 采购/销售/生产/设备等业务表')
print('  默认仓库: WH01(主仓库), WH02(辅料仓库)')
print('  默认管理员: admin / admin123')
print('=' * 50)
