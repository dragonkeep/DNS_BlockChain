from flask import jsonify, request
from functools import wraps
from database import db
from flask_jwt_extended import (
    JWTManager, create_access_token, get_jwt_identity, jwt_required
)

class UserManager:
    def __init__(self):
        self.db = db
    
    def register(self, username, password):
        return self.db.register_user(username, password)
    
    def login(self, username, password):
        return self.db.verify_user(username, password)
    
    def bind_wallet(self, username, wallet_address):
        return self.db.bind_wallet(username, wallet_address)
    
    def unbind_wallet(self, username):
        return self.db.unbind_wallet(username)
    
    def get_user_wallet(self, username):
        return self.db.get_user_wallet(username)

# 创建用户管理器实例
user_manager = UserManager()

# JWT 认证装饰器
def login_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

# 生成token的工具函数
def generate_token(username):
    return create_access_token(identity=username)