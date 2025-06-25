import sqlite3
import os
from pathlib import Path

class Database:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'data', 'user.db')
        self.init_database()
    
    def init_database(self):
        # 确保data目录存在
        Path(os.path.dirname(self.db_path)).mkdir(parents=True, exist_ok=True)
        
        # 创建数据库连接
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            wallet_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_db(self):
        return sqlite3.connect(self.db_path)
    
    def register_user(self, username, password):
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                          (username, password))
            conn.commit()
            return True, '注册成功'
        except sqlite3.IntegrityError:
            return False, '用户名已存在'
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def verify_user(self, username, password):
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            
            if result and result[0] == password:
                return True, '登录成功'
            return False, '用户名或密码错误'
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def bind_wallet(self, username, wallet_address):
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET wallet_address = ? WHERE username = ?',
                          (wallet_address, username))
            conn.commit()
            if cursor.rowcount > 0:
                return True, '钱包绑定成功'
            return False, '用户不存在'
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def unbind_wallet(self, username):
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET wallet_address = NULL WHERE username = ?',
                          (username,))
            conn.commit()
            if cursor.rowcount > 0:
                return True, '钱包解绑成功'
            return False, '用户不存在'
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def get_user_wallet(self, username):
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT wallet_address FROM users WHERE username = ?',
                          (username,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception:
            return None
        finally:
            conn.close()

# 创建数据库实例
db = Database()