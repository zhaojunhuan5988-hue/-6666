import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = 'factory-erp-secret-key-change-in-production'
DB_PATH = os.path.join(BASE_DIR, 'db', 'factory_erp.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'xlsx', 'docx'}

# 管理员默认账号
DEFAULT_ADMIN = {
    'username': 'admin',
    'password': 'admin123',
    'name': '系统管理员',
    'role': 'admin'
}
