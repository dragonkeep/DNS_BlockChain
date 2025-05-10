from flask import Flask, jsonify, request
import json
import dns
from uuid import uuid4
import threading
import time
from time import time
import atexit

"""
This layer takes care of DNS request and reponse packets
Additionally support packets adding new entries, which should require
authentication. Other routes implement methods required to maintain
integrity and consistency of the blockchain.
"""

# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the DNS resolver object
dns_resolver = dns.dns_layer(node_identifier = node_identifier)

# # 设置定期保存数据的间隔（秒）
# SAVE_INTERVAL = 300  # 5分钟保存一次

# # 定期保存数据的线程函数
# def periodic_save():
# 	while True:
# 		time.sleep(SAVE_INTERVAL)
# 		print(f"定期保存数据 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
# 		dns_resolver.save_data()

# # 启动定期保存数据的线程
# save_thread = threading.Thread(target=periodic_save, daemon=True)
# save_thread.start()

# 注册程序退出时保存数据
def save_on_exit():
	print("程序退出，保存数据...")
	dns_resolver.save_data()

atexit.register(save_on_exit)

@app.route('/debug/alive',methods=['GET'])
def check_alive():
	response = 'The node is alive'
	return  jsonify(response),200

@app.route('/nodes/new',methods=['POST'])
def register_node():
	"""
	Calls underlying functions to register new node in network
	"""
	values = request.get_json()
	nodes = values.get('nodes')

	if nodes is None:
		response,return_code = "No node supplied",400
	else:
		for node in nodes:
			dns_resolver.register_node(node)
		
		response,return_code = {
		'message': 'New nodes have been added',
		'total_nodes': dns_resolver.get_network_size(),
		},201

@app.route('/dns/register', methods=['POST'])
def register_domain():
    """
    注册新域名（使用注册区块链，需要代币和租赁）
    """
    values = request.get_json()
    required = ['hostname', 'ip', 'port', 'lease_years']
    if not all(k in values for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # 检查域名状态
    domain_status = dns_resolver.check_domain_status(values['hostname'])
    if domain_status['exists'] and not domain_status['expired']:
        return jsonify({'error': 'Domain already registered and not expired'}), 400

    # 尝试在注册区块链中注册域名（使用new_entry方法，需要代币和租赁）
    if dns_resolver.new_entry(values['hostname'], values['ip'], values['port'], values['lease_years']):
        return jsonify({'message': 'Domain registered successfully', 'blockchain_type': 'register'}), 201
    else:
        return jsonify({'error': 'Insufficient tokens'}), 400

@app.route('/dns/new',methods=['POST'])
def new_transaction():
    """
    添加新的DNS记录（使用普通DNS区块链，不需要代币和租赁）
    """
    values = request.get_json()
    required = ['hostname', 'ip', 'port']
    bad_entries = []

    for value in values:
        if all(k in values[value] for k in required):
            value = values[value]
            node_id = value.get('node_id', node_identifier)
            # 使用new_entry_without_token方法，不需要代币和租赁
            dns_resolver.new_entry_without_token(value['hostname'], value['ip'], value['port'], node_id)
        else:
            bad_entries.append(value)

    if bad_entries:
        response = {
            'bad_entries': bad_entries
        }
        return jsonify(response), 400
    else:
        response = {'message': 'New DNS entry added', 'blockchain_type': 'dns'}
        return jsonify(response), 201


@app.route('/dns/request',methods=['POST'])
def dns_lookup():
	"""
	receives a dns request and responses after resolving
	"""
	values = request.get_json()
	required = ['hostname']
	if not all(k in values for k in required):
		return 'Missing values', 400

	try:
		host,port = dns_resolver.lookup(values['hostname'])
		response = {
		'ip':host,
		'port': port
		}
		return_code = 200
	except LookupError:
		response = "No existing entry"
		return_code = 401
	
	return jsonify(response), return_code

@app.route('/nodes/resolve',methods=['GET'])
def consensus():
	"""
	触发区块链检查与其他邻居节点的链，并使用最长的链来达成共识
	可以通过type参数指定要解决冲突的区块链类型：register, dns, both
	"""
	# 获取区块链类型参数
	blockchain_type = request.args.get('type', 'both')
	
	if blockchain_type == 'register':
		# 只解决注册区块链的冲突
		t = threading.Thread(target=dns_resolver.register_blockchain.resolve_conflicts)
		t.start()
		response = {'message': f'Resolving conflicts for register blockchain'}
	elif blockchain_type == 'dns':
		# 只解决DNS区块链的冲突
		t = threading.Thread(target=dns_resolver.dns_blockchain.resolve_conflicts)
		t.start()
		response = {'message': f'Resolving conflicts for dns blockchain'}
	else:  # 'both'
		# 解决两个区块链的冲突
		t1 = threading.Thread(target=dns_resolver.register_blockchain.resolve_conflicts)
		t2 = threading.Thread(target=dns_resolver.dns_blockchain.resolve_conflicts)
		t1.start()
		t2.start()
		response = {'message': f'Resolving conflicts for both blockchains'}

	return jsonify(response), 200

@app.route('/debug/dump_chain',methods=['GET'])
@app.route('/nodes/chain',methods=['GET'])
def dump_chain():
	# 获取区块链类型参数
	blockchain_type = request.args.get('type', 'both')
	response = dns_resolver.dump_chain(blockchain_type)
	return jsonify(response), 200

@app.route('/debug/dump_buffer',methods=['GET'])
def dump_buffer():
	# 获取区块链类型参数
	blockchain_type = request.args.get('type', 'both')
	response = dns_resolver.dump_buffer(blockchain_type)
	return jsonify(response), 200

@app.route('/debug/force_block',methods=['GET'])
def force_block():
	# 获取区块链类型参数
	blockchain_type = request.args.get('type', 'both')
	
	if blockchain_type == 'register':
		response = dns_resolver.mine_register_block()
		return jsonify(f"New register blockchain block mined with proof {response}"), 200
	elif blockchain_type == 'dns':
		response = dns_resolver.mine_dns_block()
		return jsonify(f"New DNS blockchain block mined with proof {response}"), 200
	else:  # 'both'
		response = dns_resolver.mine_block()
		return jsonify(f"New blocks mined in both blockchains"), 200

@app.route('/debug/get_quota',methods=['GET'])
def get_chain_quota():
	# 获取区块链类型参数，默认为register，因为只有注册区块链有配额系统
	blockchain_type = request.args.get('type', 'register')
	response = dns_resolver.get_chain_quota(blockchain_type)
	return jsonify(response),200

@app.route('/data/save',methods=['GET'])
def save_data():
	"""
	手动触发数据保存
	"""
	dns_resolver.save_data()
	return jsonify({'status': '数据已成功保存'}), 200

@app.route('/tokens/balance',methods=['GET'])
def get_token_balance():
	"""
	获取指定节点的代币余额
	"""
	node_id = request.args.get('node_id', node_identifier)
	balance = dns_resolver.get_user_tokens(node_id)
	response = {
		'node_id': node_id,
		'balance': balance,
		'dns_entry_cost': dns_resolver.DNS_ENTRY_COST
	}
	return jsonify(response), 200

@app.route('/tokens/transfer',methods=['POST'])
def transfer_tokens():
	"""
	在节点之间转移代币
	"""
	values = request.get_json()
	required = ['from_node', 'to_node', 'amount']
	
	if not all(k in values for k in required):
		return jsonify({'error': '缺少必要的参数'}), 400
	
	# 获取参数
	from_node = values['from_node']
	to_node = values['to_node']
	amount = int(values['amount'])
	
	# 检查金额是否有效
	if amount <= 0:
		return jsonify({'error': '转账金额必须为正数'}), 400
	
	# 检查发送方是否有足够的代币
	from_balance = dns_resolver.get_user_tokens(from_node)
	if from_balance < amount:
		return jsonify({'error': '代币余额不足', 'available': from_balance, 'required': amount}), 400
	
	# 创建转账交易
	transfer_transaction = {
		'type': 'token_transfer',
		'from': from_node,
		'to': to_node,
		'amount': amount,
		'timestamp': time()
	}
	
	# 添加到区块链
	dns_resolver.blockchain.new_transaction(transfer_transaction)
	
	# 如果交易缓冲区已满，则挖掘新区块
	if len(dns_resolver.blockchain.current_transactions) >= dns_resolver.BUFFER_MAX_LEN:
		dns_resolver.mine_block()
	else:
		# 即使不挖掘新区块，也保存数据
		dns_resolver.save_data()
	
	# 返回新的余额信息
	new_from_balance = dns_resolver.get_user_tokens(from_node)
	new_to_balance = dns_resolver.get_user_tokens(to_node)
	
	response = {
		'status': '转账成功',
		'from_node': {
			'id': from_node,
			'balance': new_from_balance
		},
		'to_node': {
			'id': to_node,
			'balance': new_to_balance
		},
		'amount': amount
	}
	
	return jsonify(response), 201

if __name__ == '__main__':
	from argparse import ArgumentParser

	parser = ArgumentParser()
	# default port for DNS should be 53
	parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
	args = parser.parse_args()
	port = args.port

	app.run(host='0.0.0.0', port=port, debug=True)