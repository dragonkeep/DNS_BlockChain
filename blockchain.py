"""
Implementation referenced from https://github.com/dvf/blockchain
Modified to fit the DNS scenario
"""

import hashlib
from time import time
from uuid import uuid4
from urllib.parse import urlparse
import json
import requests

class Blockchain(object):
	def __init__(self, wallet_address):
		"""
		初始化区块链类
		
		Current_transactions 是新交易的缓冲区，在创建新区块前存储
		Chain 是区块链（账本），存储所有数据
		Nodes 是一个集合，跟踪所有其他节点
		这是必需的，因为我们需要向其他节点广播信息
		
		:param wallet_address: 钱包地址，作为节点的唯一标识符
		"""
		self.current_transactions = []
		self.chain = []
		self.nodes = set()
		self.wallet_address = wallet_address  # 使用钱包地址替代node_identifier
		self.transaction_counter = 0  # 添加交易计数器

		# 加载持久化区块链数据
		self.chain_file = "data/blockchain.json"
		self.load_chain()

		if not self.chain:
			# 创建创世区块
			# 这是一个硬编码的区块，作为第一个区块
			# 它不包含任何数据
			self.new_block(previous_hash = '1', proof=100)

	def register_node(self, address):
		"""
		添加新节点到节点列表
		
		:param address: 网络中新节点的地址
		"""
		# print(address)
		# parsed_url = urlparse(address)
		# self.nodes.add(parsed_url.netloc)
		self.nodes.add(address)
		# print(self.nodes)

	@property
	def quota(self):
		"""
		遍历链并计算我们拥有的配额（发布现金）
		现金通过特殊类型的交易记录
		"""
		chain = self.chain
		quota = 10

		for block in chain:
			own_block = (block['source'] == self.wallet_address)  # 使用钱包地址
			for transaction in block['transactions']:
				if 'wallet' in transaction and transaction['wallet'] == self.wallet_address:  # 使用钱包地址
					quota += transaction['reward']
				elif own_block:
					quota -= 1
		return quota

	@property
	def last_block(self):
		"""
		属性方法，返回链中的尾部区块
		"""
		if not self.chain:
			# 如果链为空，先创建创世区块
			self.new_block(previous_hash='1', proof=100)
			print(f"在last_block属性中创建创世区块完成")
		return self.chain[-1]

	@property
	def buffered_transaction(self):
		"""
		属性方法，返回尚未写入区块的缓冲交易列表
		"""
		return self.current_transactions

	@staticmethod
	def hash(block):
		"""
		创建区块的SHA-256哈希
		
		:param block: 区块
		"""

		# 对字典进行排序以确保哈希一致
		block_string = json.dumps(block, sort_keys=True).encode()
		return hashlib.sha256(block_string).hexdigest()

	@staticmethod
	def valid_proof(last_proof,proof):
		"""
		验证工作量证明
		在我们的场景中，不需要创建新区块的激励
		因此，POW应该容易满足
		我们使用前缀=="00"作为标准
		
		:param last_proof: 前一个证明
		:param proof: 当前证明
		:return: 如果正确则为True，否则为False
		"""
		guess = f'{last_proof}{proof}'.encode()
		guess_hash = hashlib.sha256(guess).hexdigest()
		return guess_hash[:2] == "00"

	@staticmethod
	def salt_generator():
		num = 0
		while True:
			yield num
			num += 1
			if num%100 == 0:
				print("生成盐值...")

	def proof_of_work(self, last_proof):
		"""
		工作量证明算法。迭代不同的盐值
		查看哪个盐值满足valid_proof
		"""
		salt_gen = self.salt_generator()
		salt = next(salt_gen)
		while not self.valid_proof(last_proof,salt):
			salt = next(salt_gen)
		print("POW已生成")
		return salt

	def new_transaction(self,transaction):
		"""
		创建新交易，将进入下一个挖掘的区块
		为了灵活性，我们不在这里定义交易的格式
		
		:param transaction: 我们正在添加的新交易
		:return: 当前交易缓冲区中的交易数量
		"""
		self.current_transactions.append(transaction)
		self.transaction_counter += 1  # 增加交易计数
		
		# 当交易数达到10条时，自动出块
		if self.transaction_counter >= 10:
			# 检查区块链是否为空，如果为空则先创建创世区块
			if not self.chain:
				self.new_block(previous_hash='1', proof=100)
				print(f"创建创世区块完成")
			
			last_block = self.chain[-1]  # 直接访问最后一个区块，避免使用last_block属性
			last_proof = last_block['proof']
			proof = self.proof_of_work(last_proof)
			previous_hash = self.hash(last_block)
			self.new_block(proof, previous_hash)
			self.transaction_counter = 0  # 重置计数器
			print(f"自动出块完成，区块链文件：{self.chain_file}")
		
		return len(self.current_transactions)

	def save_chain(self):
		"""
		保存区块链数据到文件，采用追加模式（a+），不覆盖原有内容
		"""
		try:
			import os
			data_dir = os.path.dirname(self.chain_file)
			if not os.path.exists(data_dir):
				os.makedirs(data_dir)
			# 先读取原有内容
			chain_data = []
			if os.path.exists(self.chain_file):
				with open(self.chain_file, 'r', encoding='utf-8') as f:
					content = f.read().strip()
					if content:
						chain_data = json.loads(content)
			# 只追加新块
			if len(chain_data) < len(self.chain):
				new_blocks = self.chain[len(chain_data):]
				chain_data.extend(new_blocks)
				with open(self.chain_file, 'w', encoding='utf-8') as f:
					json.dump(chain_data, f, indent=4, ensure_ascii=False)
			print(f"成功保存区块链数据，共 {len(self.chain)} 个区块")
		except Exception as e:
			print(f"保存区块链数据失败: {e}")

	def load_chain(self):
		"""
		从文件加载区块链数据
		"""
		try:
			import os
			if os.path.exists(self.chain_file):
				with open(self.chain_file, 'r') as f:
					import json
					self.chain = json.load(f)
				print(f"成功加载区块链数据，共 {len(self.chain)} 个区块")
			else:
				print(f"区块链数据文件不存在，创建新的区块链")
				self.chain = []
		except Exception as e:
			print(f"加载区块链数据失败: {e}")
			self.chain = []

	def new_block(self,proof,previous_hash):
		"""
		在区块链中创建新区块
		
		:param proof: 工作量证明算法给出的证明
		:param previous_hash: 前一个区块的哈希
		:return: 新区块
		"""
		# 处理previous_hash，确保在链为空时不会尝试访问self.chain[-1]
		if previous_hash is None and len(self.chain) > 0:
			previous_hash = self.hash(self.chain[-1])
			
		block = {
			'index': len(self.chain) + 1,
			'source': self.wallet_address,  # 使用钱包地址
			'timestamp': time(),
			'transactions': self.current_transactions,
			'proof': proof,
			'previous_hash': previous_hash,
		}

		# 重置当前交易列表
		self.current_transactions = []

		self.chain.append(block)
		self.save_chain()
		return block        

	def resolve_conflicts(self):
		"""
		这是我们的共识算法，它通过用网络中最长的链替换我们的链来解决冲突
		
		:return: 如果我们的链被替换则为True，否则为False
		"""

		neighbours = self.nodes
		new_chain = None

		# 我们只寻找比我们更长的链
		max_length = len(self.chain)

		# 从网络中的所有节点获取并验证链
		for node in neighbours:
			node_addr = f'http://{node}/nodes/chain'
			# print(node_addr)
			response = requests.get(node_addr)

			if response.status_code == 200:
				length = response.json()['length']
				chain = response.json()['chain']

				# 检查长度是否更长且链是否有效
				if length > max_length and self.valid_chain(chain):
					max_length = length
					new_chain = chain

		# 如果我们发现了一个新的、有效的、比我们更长的链，则替换我们的链
		if new_chain:
			self.chain = new_chain
			return True

		return False

	@classmethod
	def valid_chain(cls,chain):
		"""
		确定给定的区块链是否有效
		
		:param chain: 区块链
		:return: 如果有效则为True，否则为False
		"""

		last_block = chain[0]
		current_index = 1

		while current_index < len(chain):
			block = chain[current_index]
			print(f'{last_block}')
			print(f'{block}')
			print("\n-----------\n")
			# 检查区块的哈希是否正确
			if block['previous_hash'] != cls.hash(last_block):
				return False

			# 检查工作量证明是否正确
			if not cls.valid_proof(last_block['proof'], block['proof']):
				return False

			last_block = block
			current_index += 1

		return True




