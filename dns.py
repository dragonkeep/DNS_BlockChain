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
		Initialize blockchain objects
		BUFFER_MAX_LEN is the number of entries per block
		"""
		self.register_blockchain = bc.Blockchain(node_identifier)
		self.dns_blockchain = bc.Blockchain(node_identifier)
		self.BUFFER_MAX_LEN = 20
		self.MINE_REWARD = 10
		self.DNS_ENTRY_COST = 2  # 基础代币数量
		self.LEASE_COST_PER_YEAR = 2  # 每年租赁费用
		self.node_identifier = node_identifier
		self.data_dir = "data"
		self.tokens_file = os.path.join(self.data_dir, "tokens.json")
		self.dns_entries_file = os.path.join(self.data_dir, "dns_entries.json")
		
		# 为两个区块链设置不同的数据文件
		self.register_blockchain.chain_file = os.path.join(self.data_dir, "register_blockchain.json")
		self.dns_blockchain.chain_file = os.path.join(self.data_dir, "dns_blockchain.json")
		
		# Ensure the data directory exists
		if not os.path.exists(self.data_dir):
			os.makedirs(self.data_dir)
			
		# Load persistent data
		self.load_data()
		# Register to save data only once on exit
		atexit.register(self.save_data)

	def lookup(self,hostname):
		"""
		First look up the DNS record from the cache, if not found, then look up from both blockchains

		:param hostname: string, target hostname we are looking for
		:return: a tuple (ip,port)
		"""
		# First look up from the cache
		if hasattr(self, 'dns_entries_cache') and hostname in self.dns_entries_cache:
			entry = self.dns_entries_cache[hostname]
			return (entry['ip'], entry['port'])
			
		# 先从注册区块链中查找
		for block in self.register_blockchain.chain:
			transactions = block['transactions']
			for transaction in transactions:
				if 'hostname' in transaction and transaction['hostname'] == hostname:
					# Update cache after finding
					if hasattr(self, 'dns_entries_cache'):
						self.save_dns_entry(transaction['hostname'], transaction['ip'], transaction['port'], 
							transaction.get('node_id', self.node_identifier))
					return (transaction['ip'], transaction['port'])
		
		# 如果在注册区块链中未找到，再从普通DNS区块链中查找
		for block in self.dns_blockchain.chain:
			transactions = block['transactions']
			for transaction in transactions:
				if 'hostname' in transaction and transaction['hostname'] == hostname:
					# Update cache after finding
					if hasattr(self, 'dns_entries_cache'):
						self.save_dns_entry(transaction['hostname'], transaction['ip'], transaction['port'], 
							transaction.get('node_id', self.node_identifier))
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
		'block_index':block['index'],
		'reward':self.MINE_REWARD
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
		'block_index':block['index'],
		'reward':self.MINE_REWARD
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
				# if response.status_code != 200:
				# 	raise ValueError(f'Node {node} responded bad status code')
		
		if blockchain_type == 'dns' or blockchain_type == 'both':
			neighbors = self.dns_blockchain.nodes
			for node in neighbors:
				print(f"Requesting {node} to resolve dns blockchain")
				response = requests.get(f'http://{node}/nodes/resolve?type=dns')
				# if response.status_code != 200:
				# 	raise ValueError(f'Node {node} responded bad status code')

		print("Broadcast Complete")

	def new_entry(self,hostname,ip,port,lease_years=1,node_id=None):
		"""
		添加新的DNS记录到注册区块链的交易池，需要检查代币余额，收取代币费用。
		仅当缓冲区满时才打包到区块中。
		:param hostname: string, hostname
		:param ip: string, ip of corresponding hostname
		:param port: int, port of corresponding ip
		:param node_id: string, the node identifier who is adding this entry
		:return: bool, True if entry was added successfully, False if not enough tokens
		"""
		# If node_id is not specified, use the current node identifier
		if node_id is None:
			node_id = self.node_identifier
		# Check if the user has enough tokens
		user_tokens = self.get_user_tokens(node_id)
		try:
			lease_years = int(lease_years)
		except ValueError:
			return False
		required_tokens = self.DNS_ENTRY_COST + (self.LEASE_COST_PER_YEAR * lease_years)
		if user_tokens < required_tokens:
			return False
		# Create a new DNS record transaction
		new_transaction = {
			'hostname':hostname,
			'ip':ip,
			'port':port,
			'node_id':node_id,
            'lease_years':lease_years
		}
		buffer_len = self.register_blockchain.new_transaction(new_transaction)
		# Create a token payment transaction
		token_transaction = {
			'type': 'token_payment',
			'from': node_id,
			'amount': self.DNS_ENTRY_COST,
			'for_hostname': hostname,
			'timestamp': time()
		}
		self.register_blockchain.new_transaction(token_transaction)
		# Save DNS record to file
		self.save_dns_entry(hostname, ip, port, node_id)
		# Only mine when the buffer is full
		if buffer_len >= self.BUFFER_MAX_LEN:
			self.mine_register_block()
		return True
		
	def new_entry_without_token(self,hostname,ip,port,node_id=None,lease_years=1):
		"""
		添加新的DNS记录到普通DNS区块链的交易池，不检查代币余额，不收取代币费用。
		仅当缓冲区满时才打包到区块中。
		:param hostname: 字符串，主机名
		:param ip: 字符串，对应主机名的IP
		:param port: 整数，对应IP的端口
		:param node_id: 字符串，添加此条目的节点标识符
		:param lease_years: 整数，租赁年限
		:return: 无返回值
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
		buffer_len = self.dns_blockchain.new_transaction(new_transaction)
		# 保存DNS记录到文件
		self.save_dns_entry(hostname, ip, port, node_id)
		# 仅当缓冲区满时才挖掘新区块
		if buffer_len >= self.BUFFER_MAX_LEN:
			self.mine_dns_block()
			
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
		Load persistent data from file
		"""
		# Ensure the data directory exists
		self.ensure_data_directory()
		
		# 加载两个区块链的数据
		self.register_blockchain.load_chain()
		self.dns_blockchain.load_chain()
		print(f"Successfully loaded register blockchain data, total {len(self.register_blockchain.chain)} blocks")
		print(f"Successfully loaded DNS blockchain data, total {len(self.dns_blockchain.chain)} blocks")
		
		# Load token balances
		if os.path.exists(self.tokens_file):
			try:
				with open(self.tokens_file, 'r') as f:
					self.tokens_cache = json.load(f)
				print(f"Successfully loaded token balance data, total {len(self.tokens_cache)} records")
			except Exception as e:
				print(f"Failed to load token balance file: {e}")
				print(f"tokens_file path: {self.tokens_file}")
				try:
					with open(self.tokens_file, 'r') as f:
						print(f"tokens_file content: {f.read()}")
				except Exception as e2:
					print(f"Unable to read tokens_file content: {e2}")
				self.tokens_cache = {}
		else:
			print(f"Token balance file does not exist, creating new cache")
			print(f"tokens_file path: {self.tokens_file}")
			self.tokens_cache = {}
		
		# Load DNS records
		if os.path.exists(self.dns_entries_file):
			try:
				with open(self.dns_entries_file, 'r') as f:
					self.dns_entries_cache = json.load(f)
				print(f"Successfully loaded DNS record data, total {len(self.dns_entries_cache)} records")
			except Exception as e:
				print(f"Failed to load DNS record file: {e}")
				print(f"dns_entries_file path: {self.dns_entries_file}")
				try:
					with open(self.dns_entries_file, 'r') as f:
						print(f"dns_entries_file content: {f.read()}")
				except Exception as e2:
					print(f"Unable to read dns_entries_file content: {e2}")
				self.dns_entries_cache = {}
		else:
			print(f"DNS record file does not exist, creating new cache")
			print(f"dns_entries_file path: {self.dns_entries_file}")
			self.dns_entries_cache = {}
		
	def save_data(self):
		"""
		Save all data to file
		"""
		# Ensure the data directory exists
		self.ensure_data_directory()
		# Avoid overwriting valid data after cache is cleared due to multiple saves
		if not hasattr(self, '_data_saved') or not self._data_saved:
			# 保存两个区块链的数据
			self.register_blockchain.save_chain()
			self.dns_blockchain.save_chain()
			
			print(f"Current register blockchain length: {len(self.register_blockchain.chain)}")
			print(f"Current DNS blockchain length: {len(self.dns_blockchain.chain)}")
			
			print(f"tokens_cache before update_all_token_balances: {getattr(self, 'tokens_cache', {})}")
			self.update_all_token_balances()
			print(f"tokens_cache after update_all_token_balances: {getattr(self, 'tokens_cache', {})}")
			
			print(f"dns_entries_cache before update_all_dns_entries: {getattr(self, 'dns_entries_cache', {})}")
			self.update_all_dns_entries()
			print(f"dns_entries_cache after update_all_dns_entries: {getattr(self, 'dns_entries_cache', {})}")
			
			# Save token balance to file
			try:
				with open(self.tokens_file, 'w') as f:
					json.dump(self.tokens_cache, f, indent=4)
				print(f"Successfully saved token balance data, total {len(self.tokens_cache)} records")
			except Exception as e:
				print(f"Failed to save token balance file: {e}")
			
			# Save DNS record to file
			try:
				with open(self.dns_entries_file, 'w') as f:
					json.dump(self.dns_entries_cache, f, indent=4)
				print(f"Successfully saved DNS record data, total {len(self.dns_entries_cache)} records")
			except Exception as e:
				print(f"Failed to save DNS record file: {e}")
				
			self._data_saved = True
			
	def save_token_balance(self, node_id, balance):
		"""
		Save token balance of a single node
		:param node_id: Node ID
		:param balance: Token balance
		"""
		# Ensure the data directory exists
		self.ensure_data_directory()
		
		self.tokens_cache[node_id] = balance
		
		# Save to file every time the token balance is updated
		try:
			with open(self.tokens_file, 'w') as f:
				json.dump(self.tokens_cache, f, indent=4)
		except Exception as e:
			print(f"Failed to save token balance file: {e}")
			
	def save_dns_entry(self, hostname, ip, port, node_id):
		"""
		Save DNS record
		:param hostname: Hostname
		:param ip: IP address
		:param port: Port
		:param node_id: Node ID that created the record
		"""
		# Ensure the data directory exists
		self.ensure_data_directory()
		
		self.dns_entries_cache[hostname] = {
			'ip': ip,
			'port': port,
			'node_id': node_id,
			'timestamp': time()
		}
		
		# Save to file every time a DNS record is added
		try:
			with open(self.dns_entries_file, 'w') as f:
				json.dump(self.dns_entries_cache, f, indent=4)
		except Exception as e:
			print(f"Failed to save DNS record file: {e}")
			
	def update_all_token_balances(self):
		"""
		Update all node token balances
		"""
		# Get all node IDs
		node_ids = set()
		
		# 只从注册区块链中获取节点ID，因为代币系统只在注册区块链中使用
		# Get all node IDs from the register blockchain
		for block in self.register_blockchain.chain:
			for transaction in block['transactions']:
				if 'node' in transaction:
					node_ids.add(transaction['node'])
				if 'from' in transaction:
					node_ids.add(transaction['from'])
				if 'to' in transaction:
					node_ids.add(transaction['to'])
				if 'node_id' in transaction:
					node_ids.add(transaction['node_id'])
		
		# Update the token balance for each node
		for node_id in node_ids:
			balance = self.get_user_tokens(node_id)
			self.tokens_cache[node_id] = balance
			
	def update_all_dns_entries(self):
		"""
		Update all DNS records
		"""
		# Clear DNS record cache
		self.dns_entries_cache = {}
		
		# 从注册区块链中获取DNS记录
		for block in self.register_blockchain.chain:
			for transaction in block['transactions']:
				if 'hostname' in transaction and 'ip' in transaction and 'port' in transaction:
					hostname = transaction['hostname']
					ip = transaction['ip']
					port = transaction['port']
					node_id = transaction.get('node_id', self.node_identifier)
					lease_years = transaction.get('lease_years', 1)
					
					self.dns_entries_cache[hostname] = {
						'ip': ip,
						'port': port,
						'node_id': node_id,
						'timestamp': block['timestamp'],
						'blockchain_type': 'register',
						'lease_years': lease_years
					}
		
		# 从普通DNS区块链中获取DNS记录（如果在注册区块链中已存在相同主机名的记录，则不覆盖）
		for block in self.dns_blockchain.chain:
			for transaction in block['transactions']:
				if 'hostname' in transaction and 'ip' in transaction and 'port' in transaction:
					hostname = transaction['hostname']
					# 如果该主机名已经在注册区块链中存在，则跳过
					if hostname in self.dns_entries_cache and self.dns_entries_cache[hostname].get('blockchain_type') == 'register':
						continue
					
					ip = transaction['ip']
					port = transaction['port']
					node_id = transaction.get('node_id', self.node_identifier)
					
					self.dns_entries_cache[hostname] = {
						'ip': ip,
						'port': port,
						'node_id': node_id,
						'timestamp': block['timestamp'],
						'blockchain_type': 'dns'
					}
		
	def check_domain_status(self, hostname):
		"""
		检查域名状态
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
		
		# Save user's token balance to file
		self.save_token_balance(node_id, tokens)
				
		return tokens





