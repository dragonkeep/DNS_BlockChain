from flask import Flask
from flask_cors import CORS
from api import api
import secrets
from datetime import timedelta
from flask_jwt_extended import JWTManager

app = Flask(__name__)

def create_app():
    app = Flask(__name__)
    # 设置session密钥
    app.secret_key = secrets.token_hex(16)
    # 设置session有效期为1小时
    app.permanent_session_lifetime = timedelta(hours=1)
    # JWT配置
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-test-dev-dns-block'  # 请替换为安全的密钥
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    JWTManager(app)
    # 配置CORS，允许前端域名访问并支持credentials
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type"],
            "supports_credentials": True
        }
    })
    app.register_blueprint(api)
    return app

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    app = create_app()
    app.run(host='0.0.0.0', port=args.port, debug=True)