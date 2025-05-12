import blockchain as bc
import requests
import json
import os
from time import time
"""
Define the format of DNS transaction here
dns_transaction = {
	'hostname':hostname,
	'ip':ip,
	'port':port
}
"""
import atexit

class dns_layer(object):
	def __init__(self, node_identifier):
		"""
		初始化区块链对象
		BUFFER_MAX_LEN是每个区块的条目数
		"""
		self.register_blockchain = bc.Blockchain(node_identifier)
		self.dns_blockchain = bc.Blockchain(node_identifier)
		self.BUFFER_MAX_LEN = 10  # 修改为10条交易自动出块
		self.MINE_REWARD = 10
		self.node_identifier = node_identifier
		self.data_dir = "data"
		
		# 为两个区块链设置不同的数据文件
		self.register_blockchain.chain_file = os.path.join(self.data_dir, "register.json")  # 修改文件名
		self.dns_blockchain.chain_file = os.path.join(self.data_dir, "domains.json")  # 修改文件名
		
		# 确保数据目录存在
		if not os.path.exists(self.data_dir):
			os.makedirs(self.data_dir)
			
		# 加载持久化数据
		self.load_data()
		# 注册退出时只保存一次数据
		atexit.register(self.save_data)

	def lookup(self,hostname):
		"""
		直接从区块链中查找DNS记录

		:param hostname: string, 要查找的目标主机名
		:return: 一个元组 (ip,port)
		"""
		# 先从注册区块链中查找
		for block in self.register_blockchain.chain:
			transactions = block['transactions']
			for transaction in transactions:
				if 'hostname' in transaction and transaction['hostname'] == hostname:
					return (transaction['ip'], transaction['port'])
		
		# 如果在注册区块链中未找到，再从普通DNS区块链中查找
		for block in self.dns_blockchain.chain:
			transactions = block['transactions']
			for transaction in transactions:
				if 'hostname' in transaction and transaction['hostname'] == hostname:
					return (transaction['ip'], transaction['port'])
					
		raise LookupError('No existing entry matching hostname')

	def mine_register_block(self):
		"""
		挖掘注册区块链的新区块
		"""
		last_block = self.register_blockchain.last_block
		last_proof = last_block['proof']
		proof = self.register_blockchain.proof_of_work(last_proof)

		# Forge the new Block by adding it to the chain
		previous_hash = self.register_blockchain.hash(last_block)
		block = self.register_blockchain.new_block(proof, previous_hash)

		# broadcast request for all neighbor to resolve conflict
		self.broadcast_new_block(blockchain_type='register')

		# now add a special transaction that signifies the reward mechanism
		new_transaction = {
		'node':self.node_identifier,
		'block_index':block['index']
		}
		self.register_blockchain.new_transaction(new_transaction)
		
		# Save blockchain data
		self.save_data()
		
		return proof
		
	def mine_dns_block(self):
		"""
		挖掘普通DNS区块链的新区块
		"""
		last_block = self.dns_blockchain.last_block
		last_proof = last_block['proof']
		proof = self.dns_blockchain.proof_of_work(last_proof)

		# Forge the new Block by adding it to the chain
		previous_hash = self.dns_blockchain.hash(last_block)
		block = self.dns_blockchain.new_block(proof, previous_hash)

		# broadcast request for all neighbor to resolve conflict
		self.broadcast_new_block(blockchain_type='dns')

		# now add a special transaction that signifies the reward mechanism
		new_transaction = {
		'node':self.node_identifier,
		'block_index':block['index']
		}
		self.dns_blockchain.new_transaction(new_transaction)
		
		# Save blockchain data
		self.save_data()
		
		return proof
		
	def mine_block(self):
		"""
		为了向后兼容，保留此方法，默认挖掘两个区块链
		"""
		proof1 = self.mine_register_block()
		proof2 = self.mine_dns_block()
		return proof1

	def broadcast_new_block(self, blockchain_type='both'):
		"""
		Broadcast resolve request to all neighbor to force neighbors
		update their chain
		:param blockchain_type: 指定要广播的区块链类型，可选值：'register', 'dns', 'both'
		"""
		if blockchain_type == 'register' or blockchain_type == 'both':
			neighbors = self.register_blockchain.nodes
			for node in neighbors:
				print(f"Requesting {node} to resolve register blockchain")
				response = requests.get(f'http://{node}/nodes/resolve?type=register')
		
		if blockchain_type == 'dns' or blockchain_type == 'both':
			neighbors = self.dns_blockchain.nodes
			for node in neighbors:
				print(f"Requesting {node} to resolve dns blockchain")
				response = requests.get(f'http://{node}/nodes/resolve?type=dns')

		print("Broadcast Complete")

	def new_entry(self, hostname, ip, port, blockchain_type='register', lease_years=1, node_id=None):
		"""
		添加新的DNS记录到指定区块链的交易池
		:param hostname: string, 主机名
		:param ip: string, 对应主机名的IP
		:param port: int, 对应IP的端口
		:param blockchain_type: string, 区块链类型，可选值：'register'或'dns'
		:param lease_years: int, 租赁年限
		:param node_id: string, 添加此条目的节点标识符
		:return: bool, 如果条目添加成功则为True
		"""
		# 如果未指定node_id，使用当前节点标识符
		if node_id is None:
			node_id = self.node_identifier
		try:
			lease_years = int(lease_years)
		except ValueError:
			lease_years = 1
		# 创建新的DNS记录交易
		new_transaction = {
			'hostname':hostname,
			'ip':ip,
			'port':port,
			'node_id':node_id,
            'lease_years':lease_years
		}
		
		# 根据区块链类型选择添加到对应的区块链
		if blockchain_type.lower() == 'dns':
			# 添加到DNS区块链
			print(blockchain_type)
			buffer_len = self.dns_blockchain.new_transaction(new_transaction)
			# 仅当缓冲区满时才挖掘新区块
			if buffer_len >= self.BUFFER_MAX_LEN:
				self.mine_dns_block()
			return True
		if blockchain_type.lower() == 'register':
			# 默认添加到注册区块链
			buffer_len = self.register_blockchain.new_transaction(new_transaction)
			# 仅当缓冲区满时才挖掘新区块
			if buffer_len >= self.BUFFER_MAX_LEN:
				self.mine_register_block()
			return True
			
	def dump_chain(self, blockchain_type='both'):
		"""
		导出区块链数据
		:param blockchain_type: 指定要导出的区块链类型，可选值：'register', 'dns', 'both'
		"""
		if blockchain_type == 'register':
			response = {
			'chain': self.register_blockchain.chain,
			'length': len(self.register_blockchain.chain)
			}
		elif blockchain_type == 'dns':
			response = {
			'chain': self.dns_blockchain.chain,
			'length': len(self.dns_blockchain.chain)
			}
		else:  # 'both'
			response = {
			'register_chain': self.register_blockchain.chain,
			'register_length': len(self.register_blockchain.chain),
			'dns_chain': self.dns_blockchain.chain,
			'dns_length': len(self.dns_blockchain.chain)
			}
		return response

	def dump_buffer(self, blockchain_type='both'):
		"""
		导出交易缓冲区数据
		:param blockchain_type: 指定要导出的区块链类型，可选值：'register', 'dns', 'both'
		"""
		if blockchain_type == 'register':
			return self.register_blockchain.current_transactions
		elif blockchain_type == 'dns':
			return self.dns_blockchain.current_transactions
		else:  # 'both'
			return {
				'register': self.register_blockchain.current_transactions,
				'dns': self.dns_blockchain.current_transactions
			}

	def get_chain_quota(self, blockchain_type='register'):
		"""
		获取区块链配额
		:param blockchain_type: 指定要获取配额的区块链类型，默认为'register'
		"""
		if blockchain_type == 'register':
			return self.register_blockchain.quota
		elif blockchain_type == 'dns':
			return self.dns_blockchain.quota
		else:  # 'both'
			return {
				'register': self.register_blockchain.quota,
				'dns': self.dns_blockchain.quota
			}

	def register_node(self, addr, blockchain_type='both'):
		"""
		注册节点
		:param addr: 节点地址
		:param blockchain_type: 指定要注册节点的区块链类型，可选值：'register', 'dns', 'both'
		"""
		if blockchain_type == 'register' or blockchain_type == 'both':
			self.register_blockchain.register_node(addr)
		if blockchain_type == 'dns' or blockchain_type == 'both':
			self.dns_blockchain.register_node(addr)

	def get_network_size(self, blockchain_type='both'):
		"""
		获取网络大小
		:param blockchain_type: 指定要获取网络大小的区块链类型，可选值：'register', 'dns', 'both'
		"""
		if blockchain_type == 'register':
			return len(self.register_blockchain.nodes)
		elif blockchain_type == 'dns':
			return len(self.dns_blockchain.nodes)
		else:  # 'both'
			# 返回两个区块链节点的并集大小
			all_nodes = set()
			all_nodes.update(self.register_blockchain.nodes)
			all_nodes.update(self.dns_blockchain.nodes)
			return len(all_nodes)
		
	# Data persistence related methods
	def ensure_data_directory(self):
		"""
		Ensure the data directory exists
		"""
		if not os.path.exists(self.data_dir):
			try:
				os.makedirs(self.data_dir)
				print(f"Data directory created: {self.data_dir}")
			except Exception as e:
				print(f"Failed to create data directory: {e}")
				
	def load_data(self):
		"""
		从文件加载区块链数据
		"""
		# 确保数据目录存在
		self.ensure_data_directory()
		
		# 只加载两个区块链的数据
		self.register_blockchain.load_chain()
		self.dns_blockchain.load_chain()
		print(f"成功加载注册区块链数据，共 {len(self.register_blockchain.chain)} 个区块")
		print(f"成功加载DNS区块链数据，共 {len(self.dns_blockchain.chain)} 个区块")
		
	def save_data(self):
		"""
		保存区块链数据到文件
		"""
		# 确保数据目录存在
		self.ensure_data_directory()
		# 避免多次保存导致数据覆盖
		if not hasattr(self, '_data_saved') or not self._data_saved:
			# 直接保存两个区块链的数据到对应文件
			self.register_blockchain.save_chain()
			self.dns_blockchain.save_chain()
			
			print(f"当前注册区块链长度: {len(self.register_blockchain.chain)}")
			print(f"当前DNS区块链长度: {len(self.dns_blockchain.chain)}")
						
			self._data_saved = True
			

		
	def check_domain_status(self, hostname):
		"""
		检查域名状态，直接从区块链查询
		:param hostname: 要检查的域名
		:return: 返回字典 {'exists': bool, 'expired': bool, 'blockchain_type': str}
		"""
		# 首先在注册区块链中查找域名（带有租赁信息）
		for block in self.register_blockchain.chain:
			for transaction in block['transactions']:
				if 'hostname' in transaction and transaction['hostname'] == hostname:
					# 检查租赁是否过期
					current_time = time()
					lease_end = block['timestamp'] + (transaction.get('lease_years', 1) * 31536000)
					return {'exists': True, 'expired': current_time > lease_end, 'blockchain_type': 'register'}
		
		# 如果在注册区块链中未找到，再在普通DNS区块链中查找
		for block in self.dns_blockchain.chain:
			for transaction in block['transactions']:
				if 'hostname' in transaction and transaction['hostname'] == hostname:
					# 普通DNS记录没有过期概念
					return {'exists': True, 'expired': False, 'blockchain_type': 'dns'}
					
		return {'exists': False, 'expired': False, 'blockchain_type': None}

	def get_user_tokens(self, node_id):
		"""
		Calculate the user's token balance
		:param node_id: string, user's node identifier
		:return: int, user's token balance
		"""
		tokens = 10  # Initial token amount
		
		# 只从注册区块链中计算代币余额，因为代币系统只在注册区块链中使用
		# Traverse all blocks in the register blockchain
		for block in self.register_blockchain.chain:
			for transaction in block['transactions']:
				# Mining reward
				if 'node' in transaction and transaction['node'] == node_id and 'reward' in transaction:
					tokens += transaction['reward']
				# Token payment
				elif 'type' in transaction and transaction['type'] == 'token_payment' and transaction['from'] == node_id:
					tokens -= transaction['amount']
				# Token transfer - sender
				elif 'type' in transaction and transaction['type'] == 'token_transfer' and transaction['from'] == node_id:
					tokens -= transaction['amount']
				# Token transfer - receiver
				elif 'type' in transaction and transaction['type'] == 'token_transfer' and transaction['to'] == node_id:
					tokens += transaction['amount']
		
		# Check current unconfirmed transactions in register blockchain
		for transaction in self.register_blockchain.current_transactions:
			# Token payment
			if 'type' in transaction and transaction['type'] == 'token_payment' and transaction['from'] == node_id:
				tokens -= transaction['amount']
			# Token transfer - sender
			elif 'type' in transaction and transaction['type'] == 'token_transfer' and transaction['from'] == node_id:
				tokens -= transaction['amount']
			# Token transfer - receiver
			elif 'type' in transaction and transaction['type'] == 'token_transfer' and transaction['to'] == node_id:
				tokens += transaction['amount']
		
				
		return tokens