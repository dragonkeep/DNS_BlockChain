from configparser import NoSectionError
from flask import Blueprint, jsonify, request, session
import json
import os
import dns
import threading
import time as _time
import atexit
from blockwallet import Wallet
from functools import wraps
from login import user_manager, login_required
# Blueprint for API endpoints
api = Blueprint('api', __name__)

# 创建默认钱包作为节点标识符
default_wallet = None
wallet_address = None
dns_resolver = None
wallet_status = False
init_balance = 10
# 初始化函数，检查是否有已保存的钱包数据
def init_wallet_from_storage():
    global default_wallet, wallet_address, dns_resolver
    try:
        from os import path
        import json
        from blockwallet import Wallet
        
        data_dir = path.join(path.dirname(__file__), 'data')
        wallet_file = path.join(data_dir, 'wallet.json')
        
        if path.exists(wallet_file):
            with open(wallet_file, 'r') as f:
                wallet_list = json.load(f)
                if wallet_list and len(wallet_list) > 0:
                    # 使用最后一个钱包地址
                    last_wallet = wallet_list[-1]
                    wallet_address = last_wallet.get('address')
                    if wallet_address:
                        dns_resolver = dns.dns_layer(node_identifier=wallet_address)
                        print(f"已从存储中恢复钱包: {wallet_address}")
                        return True
    except Exception as e:
        print(f"加载钱包数据失败: {str(e)}")
    return False

# 尝试从存储中初始化钱包
init_wallet_from_storage()

# 检测是否存在默认钱包
def require_wallet_registered(func):
    """
    Decorator to check if a wallet is registered before allowing endpoint access
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        global wallet_address, dns_resolver
        if wallet_address is None or dns_resolver is None:
            return jsonify({'error': '系统钱包未注册，请先注册钱包'}), 403
        return func(*args, **kwargs)
    return wrapper
# 注册程序退出时保存数据
# @atexit.register
# def save_on_exit():
#     print("程序退出，保存数据...")
#     dns_resolver.save_data()

@api.route('/wallet/status', methods=['GET'])
def check_wallet_status():
    """检查钱包连接状态"""
    global wallet_address, dns_resolver,wallet_status
    if wallet_status:
        return jsonify({
            'connected': True,
            'address': wallet_address,
            'message': '钱包已连接'
        }), 200
    return jsonify({
        'connected': False,
        'message': '系统钱包未注册'

    }, 200)

@api.route('/user/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    try:
        success, message = user_manager.register(username, password)
        if success:
            return jsonify({'message': message}), 201
        return jsonify({'error': message}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api.route('/user/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    try:
        success, message = user_manager.login(username, password)
        if success:
            session['username'] = username
            wallet_address = user_manager.get_user_wallet(username)
            return jsonify({
                'message':message,
                'wallet_address': wallet_address
            }), 200
        return jsonify({'error': message}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api.route('/user/logout', methods=['POST'])
def logout():
    username = session.get('username')
    if username:
        # 解绑钱包
        user_manager.unbind_wallet(username)
        session.pop('username', None)
    return jsonify({'message': '退出成功'}), 200

@api.route('/user/status', methods=['GET'])
def check_user_status():
    """检查用户登录状态"""
    username = session.get('username')
    if username:
        wallet_address = user_manager.get_user_wallet(username)
        return jsonify({
            'logged_in': True,
            'username': username,
            'wallet_address': wallet_address
        }), 200
    return jsonify({
        'logged_in': False
    }), 200

@api.route('/debug/alive', methods=['GET'])
def check_alive():
    return jsonify('The node is alive'), 200

@api.route('/nodes/new', methods=['POST'])
@require_wallet_registered
def register_node():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return jsonify('No node supplied'), 400
    for node in nodes:
        dns_resolver.register_node(node)
    return jsonify({
        'message': 'New nodes have been added',
        'total_nodes': dns_resolver.get_network_size()
    }), 201

@api.route('/user/bind-wallet', methods=['POST'])
@login_required
def bind_wallet():
    username = session.get('username')
    data = request.get_json()
    wallet_address = data.get('wallet_address')
    
    if not wallet_address:
        return jsonify({'error': '钱包地址不能为空'}), 400
    
    success, message = user_manager.bind_wallet(username, wallet_address)
    if success:
        return jsonify({'message': message}), 200
    return jsonify({'error': message}), 400

@api.route('/user/unbind-wallet', methods=['POST'])
@login_required
def unbind_wallet():
    username = session.get('username')
    if not username:
        return jsonify({'error': '用户未登录'}), 401
    
    success, message = user_manager.unbind_wallet(username)
    if success:
        return jsonify({'message': message}), 200
    return jsonify({'error': message}), 400

@api.route('/dns/register', methods=['POST'])
@require_wallet_registered
def register_domain():
    global default_wallet
    values = request.get_json()
    required = ['hostname', 'ip', 'port', 'lease_years']
    if not all(k in values for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    status = dns_resolver.check_domain_status(values['hostname'])
    if status['exists'] and not status.get('expired', False):
        if not status.get('on_chain', True):
            return jsonify({'error': 'Domain is pending and not on chain yet'}), 400
        return jsonify({'error': 'Domain already registered and not expired'}), 400

    # 增加代币余额校验
    wallet_addr = values.get('wallet_address', wallet_address)
    lease_years = int(values['lease_years'])
    cost = lease_years * 2
    balance = default_wallet.get_balance()
    if balance < cost:
        return jsonify({'error': f'Insufficient balance: {balance}, required: {cost}'}), 400

    dns_resolver.new_entry(values['hostname'], values['ip'], values['port'], 'register', lease_years, wallet_addr)
    default_wallet.add_balance(-cost)
    return jsonify({'message': 'Domain registered successfully, waiting for on-chain confirmation', 'blockchain_type': 'register', 'on_chain': False}), 201

@api.route('/dns/new', methods=['POST'])
@require_wallet_registered
def new_transaction():
    global default_wallet
    values = request.get_json()
    #print(values)
    required = ['hostname', 'ip', 'port']
    bad_entries = []
    for entry in values.values():
        if all(k in entry for k in required):
            wallet_addr = entry.get('wallet_address', wallet_address)
            default_wallet.add_balance(1)
            dns_resolver.new_entry(entry['hostname'], entry['ip'], entry['port'], 'dns', 1, wallet_addr)
        else:
            bad_entries.append(entry)
    if bad_entries:
        return jsonify({'bad_entries': bad_entries}), 400
    return jsonify({'message': 'New DNS entry added', 'blockchain_type': 'dns'}), 201

@api.route('/dns/request', methods=['POST'])
@require_wallet_registered
def dns_lookup():
    values = request.get_json()
    if 'hostname' not in values:
        return jsonify({'error': 'Missing values', 'on_chain': False}), 400
    try:
        host, port, on_chain = dns_resolver.lookup(values['hostname'])
        if not on_chain:
            return jsonify({'ip': host, 'port': port, 'on_chain': False, 'message': '该DNS记录未上链'}), 200
        return jsonify({'ip': host, 'port': port, 'on_chain': True}), 200
    except LookupError:
        return jsonify({'error': '未找到该域名', 'on_chain': False}), 404

@api.route('/nodes/resolve', methods=['GET'])
@require_wallet_registered
def consensus():
    btype = request.args.get('type', 'both')
    threads = []
    if btype in ('register', 'both'):
        t = threading.Thread(target=dns_resolver.register_blockchain.resolve_conflicts)
        threads.append(t)
        t.start()
    if btype in ('dns', 'both'):
        t = threading.Thread(target=dns_resolver.dns_blockchain.resolve_conflicts)
        threads.append(t)
        t.start()
    return jsonify({'message': f'Resolving conflicts for {btype} blockchain(s)'}), 200

@api.route('/nodes/chain', methods=['GET'])
@require_wallet_registered
def dump_chain():
    btype = request.args.get('type', 'both')
    return jsonify(dns_resolver.dump_chain(btype)), 200

@api.route('/debug/dump_buffer', methods=['GET'])
@require_wallet_registered
def dump_buffer():
    btype = request.args.get('type', 'both')
    return jsonify(dns_resolver.dump_buffer(btype)), 200

@api.route('/debug/force_block', methods=['GET'])
@require_wallet_registered
def force_block():
    btype = request.args.get('type', 'both')
    if btype == 'register':
        proof = dns_resolver.mine_register_block()
        return jsonify(f"New register blockchain block mined with proof {proof}"), 200
    if btype == 'dns':
        proof = dns_resolver.mine_dns_block()
        return jsonify(f"New DNS blockchain block mined with proof {proof}"), 200
    dns_resolver.mine_block()
    return jsonify('New blocks mined in both blockchains'), 200

@api.route('/debug/get_quota', methods=['GET'])
@require_wallet_registered
def get_chain_quota():
    btype = request.args.get('type', 'register')
    return jsonify(dns_resolver.get_chain_quota(btype)), 200

@api.route('/data/save', methods=['GET'])
@require_wallet_registered
def save_data():
    dns_resolver.save_data()
    return jsonify({'status': '数据已成功保存'}), 200

@api.route('/wallet/create', methods=['POST'])
def create_wallet():
    global default_wallet, wallet_address, dns_resolver,wallet_status
    default_wallet = Wallet()
    wallet_address = default_wallet.address
    dns_resolver = dns.dns_layer(node_identifier=wallet_address)
    # 定义数据目录路径
    from os import path
    data_dir = path.join(path.dirname(__file__), 'data')
    # 将钱包地址和余额写入wallet.json文件
    wallet_data = {
        "address": wallet_address,
        "balance": init_balance  # 初始余额为0
    }
    wallet_file = path.join(data_dir, 'wallet.json')
    if path.exists(wallet_file):
        with open(wallet_file, 'r+') as f:
            data = json.load(f)
            data.append(wallet_data)
            f.seek(0)
            json.dump(data, f, indent=4)
    else:
        with open(wallet_file, 'w') as f:
            json.dump([wallet_data], f, indent=4)
    wallet_status = True
    return jsonify({'address': default_wallet.address, 'private_key': default_wallet.private_key}), 200

@api.route('/wallet/import', methods=['POST'])
def import_wallet():
    global wallet_status
    data = request.json or {}
    pk = data.get('private_key')
    if not pk:
        return jsonify({'error': '未提供私钥'}), 400
    try:
        global default_wallet, wallet_address, dns_resolver
        default_wallet = Wallet(private_key=pk)
        wallet_address = default_wallet.address
        dns_resolver = dns.dns_layer(node_identifier=wallet_address)
        
        # 定义数据目录路径
        from os import path
        data_dir = path.join(path.dirname(__file__), 'data')
        
        # 检查钱包地址是否已存在于wallet.json文件中
        wallet_file = path.join(data_dir, 'wallet.json')
        wallet_exists = False
        
        if path.exists(wallet_file):
            with open(wallet_file, 'r+') as f:
                wallet_list = json.load(f)
                # 检查钱包地址是否已存在
                for wallet in wallet_list:
                    if wallet.get('address') == wallet_address:
                        wallet_exists = True
                        break
                
                # 如果钱包不存在，则添加到列表中
                if not wallet_exists:
                    wallet_data = {
                        "address": wallet_address,
                        "balance": init_balance  
                    }
                    wallet_list.append(wallet_data)
                    f.seek(0)
                    json.dump(wallet_list, f, indent=4)
            # wallet_status = True
        else:
            # 如果文件不存在，创建新文件并添加钱包
            wallet_data = {
                "address": wallet_address,
                "balance": init_balance 
            }
            with open(wallet_file, 'w') as f:
                json.dump([wallet_data], f, indent=4)
        return jsonify({'address': default_wallet.address}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@api.route('/wallet/info/<address>', methods=['GET'])
def get_wallet_info(address):
    from os import path
    from blockwallet import Wallet
    if not Wallet.validate_address(address):
        return jsonify({'error': '无效的钱包地址'}), 400

    data_dir = path.join(path.dirname(__file__), 'data')
    domains = []
    resolver = dns.dns_layer(node_identifier=address)
    # 注册区块链数据文件路径
    dom_file = path.join(data_dir, 'register.json')

    # 尝试加载钱包
    wallet_file = path.join(data_dir, 'wallet.json')
    wallet_found = False
    if path.exists(wallet_file):
        with open(wallet_file, 'r') as f:
            wallet_list = json.load(f)
            for w in wallet_list:
                if w.get('address') == address:
                    wallet_found = True
                    break
    if not wallet_found:
        return jsonify({'error': '未找到该钱包地址'}), 404

    # 创建钱包实例
    try:
        wallet = Wallet()
        wallet.address = address
    except Exception as e:
        return jsonify({'error': f'钱包实例化失败: {str(e)}'}), 500

    if path.exists(dom_file):
        with open(dom_file, 'r') as f:
            blockchain_data = json.load(f)
        for block in blockchain_data:
            for transaction in block.get('transactions', []):
                if transaction.get('node_id') == address:
                    domains.append({
                        'hostname': transaction['hostname'],
                        'ip': transaction['ip'],
                        'port': transaction['port'],
                        'lease_years': transaction['lease_years'],
                        'block_index': block['index'],
                        'timestamp': block['timestamp']
                    })

    # 获取余额
    try:
        balance = wallet.get_balance()
    except Exception:
        balance = 0

    return jsonify({
        'address': address,
        'domains': domains,
        'count': len(domains),
        'balance': balance
    }), 200

@api.route('/wallet/reset', methods=['POST'])
def reset_wallet_data():
    from os import path, remove
    data_dir = path.join(path.dirname(__file__), 'data')
    dom_file = path.join(data_dir, 'domains.json')
    if path.exists(dom_file): remove(dom_file)
    return jsonify({'message': '钱包数据已重置'}), 200

@api.route('/wallet/disconnect', methods=['POST'])
def disconnect_wallet():
    global wallet_status, wallet_address, default_wallet, dns_resolver
    wallet_status = False
    wallet_address = None
    default_wallet = None
    dns_resolver = None
    return jsonify({'message': '钱包已断开连接'}), 200