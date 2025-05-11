from flask import Blueprint, jsonify, request
import json
import os
import dns
from uuid import uuid4
import threading
import time as _time
import atexit
from blockwallet import Wallet

# Blueprint for API endpoints
api = Blueprint('api', __name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the DNS resolver object
dns_resolver = dns.dns_layer(node_identifier=node_identifier)

# 注册程序退出时保存数据
@atexit.register
def save_on_exit():
    print("程序退出，保存数据...")
    dns_resolver.save_data()

@api.route('/debug/alive', methods=['GET'])
def check_alive():
    return jsonify('The node is alive'), 200

@api.route('/nodes/new', methods=['POST'])
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

@api.route('/dns/register', methods=['POST'])
def register_domain():
    values = request.get_json()
    required = ['hostname', 'ip', 'port', 'lease_years']
    if not all(k in values for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    status = dns_resolver.check_domain_status(values['hostname'])
    if status['exists'] and not status['expired']:
        return jsonify({'error': 'Domain already registered and not expired'}), 400

    if dns_resolver.new_entry(values['hostname'], values['ip'], values['port'], values['lease_years']):
        return jsonify({'message': 'Domain registered successfully', 'blockchain_type': 'register'}), 201
    else:
        return jsonify({'error': 'Insufficient tokens'}), 400

@api.route('/dns/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['hostname', 'ip', 'port']
    bad_entries = []
    for entry in values.values():
        if all(k in entry for k in required):
            node_id = entry.get('node_id', node_identifier)
            dns_resolver.new_entry_without_token(entry['hostname'], entry['ip'], entry['port'], node_id)
        else:
            bad_entries.append(entry)
    if bad_entries:
        return jsonify({'bad_entries': bad_entries}), 400
    return jsonify({'message': 'New DNS entry added', 'blockchain_type': 'dns'}), 201

@api.route('/dns/request', methods=['POST'])
def dns_lookup():
    values = request.get_json()
    if 'hostname' not in values:
        return jsonify('Missing values'), 400
    try:
        host, port = dns_resolver.lookup(values['hostname'])
        return jsonify({'ip': host, 'port': port}), 200
    except LookupError:
        return jsonify('No existing entry'), 401

@api.route('/nodes/resolve', methods=['GET'])
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
def dump_chain():
    btype = request.args.get('type', 'both')
    return jsonify(dns_resolver.dump_chain(btype)), 200

@api.route('/debug/dump_buffer', methods=['GET'])
def dump_buffer():
    btype = request.args.get('type', 'both')
    return jsonify(dns_resolver.dump_buffer(btype)), 200

@api.route('/debug/force_block', methods=['GET'])
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
def get_chain_quota():
    btype = request.args.get('type', 'register')
    return jsonify(dns_resolver.get_chain_quota(btype)), 200

@api.route('/data/save', methods=['GET'])
def save_data():
    dns_resolver.save_data()
    return jsonify({'status': '数据已成功保存'}), 200

@api.route('/tokens/balance', methods=['GET'])
def get_token_balance():
    node_id = request.args.get('node_id', node_identifier)
    balance = dns_resolver.get_user_tokens(node_id)
    return jsonify({'node_id': node_id, 'balance': balance, 'dns_entry_cost': dns_resolver.DNS_ENTRY_COST}), 200

@api.route('/tokens/transfer', methods=['POST'])
def transfer_tokens():
    values = request.get_json()
    required = ['from_node', 'to_node', 'amount']
    if not all(k in values for k in required):
        return jsonify({'error': '缺少必要的参数'}), 400
    frm, to, amt = values['from_node'], values['to_node'], int(values['amount'])
    if amt <= 0:
        return jsonify({'error': '转账金额必须为正数'}), 400
    if dns_resolver.get_user_tokens(frm) < amt:
        return jsonify({'error': '代币余额不足', 'available': dns_resolver.get_user_tokens(frm), 'required': amt}), 400
    tx = {'type': 'token_transfer', 'from': frm, 'to': to, 'amount': amt, 'timestamp': _time.time()}
    dns_resolver.blockchain.new_transaction(tx)
    if len(dns_resolver.blockchain.current_transactions) >= dns_resolver.BUFFER_MAX_LEN:
        dns_resolver.mine_block()
    else:
        dns_resolver.save_data()
    return jsonify({'status': '转账成功','from_node': {'id': frm,'balance': dns_resolver.get_user_tokens(frm)},'to_node': {'id': to,'balance': dns_resolver.get_user_tokens(to)},'amount': amt}), 201

@api.route('/wallet/create', methods=['POST'])
def create_wallet():
    wallet = Wallet()
    return jsonify({'address': wallet.address, 'private_key': wallet.private_key}), 200

@api.route('/wallet/import', methods=['POST'])
def import_wallet():
    data = request.json or {}
    pk = data.get('private_key')
    if not pk:
        return jsonify({'error': '未提供私钥'}), 400
    try:
        wallet = Wallet(private_key=pk)
        return jsonify({'address': wallet.address}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@api.route('/wallet/info/<address>', methods=['GET'])
def get_wallet_info(address):
    from os import path
    if not Wallet.validate_address(address):
        return jsonify({'error': '无效的钱包地址'}), 400
    data_dir = path.join(path.dirname(__file__), 'data')
    balance = 0.0
    bal_file = path.join(data_dir, 'balances.json')
    if path.exists(bal_file):
        with open(bal_file) as f:
            balance = json.load(f).get(address, 0.0)
    domains = []
    dom_file = path.join(data_dir, 'domains.json')
    if path.exists(dom_file):
        all_dom = json.load(open(dom_file))
        domains = [d for d in all_dom if d.get('owner') == address]
    return jsonify({'address': address, 'balance': balance, 'domains': domains}), 200

@api.route('/wallet/reset', methods=['POST'])
def reset_wallet_data():
    from os import path, remove
    data_dir = path.join(path.dirname(__file__), 'data')
    bal_file = path.join(data_dir, 'balances.json')
    dom_file = path.join(data_dir, 'domains.json')
    if path.exists(bal_file): remove(bal_file)
    if path.exists(dom_file): remove(dom_file)
    return jsonify({'message': '钱包数据已重置'}), 200