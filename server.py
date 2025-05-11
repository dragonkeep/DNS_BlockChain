from flask import Flask
from flask_cors import CORS
from api import api

def create_app():
    app = Flask(__name__)
    # 添加CORS支持
    CORS(app, resources={
        r"/*": {
            "origins": "*",  # 允许所有来源访问
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
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