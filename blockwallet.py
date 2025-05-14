import os
import json
import hashlib
import binascii
import ecdsa
import time
from typing import Dict, List, Tuple, Optional
from blockchain import Blockchain
from dns import dns_layer


class Wallet:
    """
    钱包类，实现BTC相同的算法生成钱包地址和私钥，
    并提供钱包相关功能
    """
    
    def __init__(self, private_key: str = None):
        """
        初始化钱包，可选择导入私钥或生成新钱包
        
        Args:
            private_key: 可选，要导入的私钥
        """
        self.private_key = private_key
        self.public_key = None
        self.address = None
        
        if private_key:
            self._import_wallet(private_key)
        else:
            self._generate_new_wallet()
            
        # 数据存储路径
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 获取区块链实例
        self.node_identifier = self.address  # 使用钱包地址作为节点标识符
        
    def _generate_new_wallet(self):
        """生成新的钱包地址和私钥"""
        # 生成一个新的私钥 (使用 ECDSA SECP256k1 曲线，与比特币相同)
        sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self.private_key = sk.to_string().hex()
        
        # 从私钥生成公钥
        vk = sk.get_verifying_key()
        self.public_key = vk.to_string().hex()
        
        # 从公钥生成地址 (类似比特币的地址生成算法)
        public_key_bytes = binascii.unhexlify(self.public_key)
        sha256_hash = hashlib.sha256(public_key_bytes).digest()
        ripemd160_hash = hashlib.new('ripemd160')
        ripemd160_hash.update(sha256_hash)
        self.address = 'DC' + binascii.hexlify(ripemd160_hash.digest()).decode('utf-8')
        
    def _import_wallet(self, private_key: str):
        """从私钥导入钱包"""
        try:
            # 从私钥重建公钥
            sk = ecdsa.SigningKey.from_string(
                binascii.unhexlify(private_key),
                curve=ecdsa.SECP256k1
            )
            self.private_key = private_key
            
            # 生成公钥
            vk = sk.get_verifying_key()
            self.public_key = vk.to_string().hex()
            
            # 从公钥生成地址
            public_key_bytes = binascii.unhexlify(self.public_key)
            sha256_hash = hashlib.sha256(public_key_bytes).digest()
            ripemd160_hash = hashlib.new('ripemd160')
            ripemd160_hash.update(sha256_hash)
            self.address = 'DC' + binascii.hexlify(ripemd160_hash.digest()).decode('utf-8')
        except Exception as e:
            raise ValueError(f"无效的私钥: {str(e)}")
            
    def get_info(self) -> Dict:
        """
        获取钱包信息，包括地址、余额和域名
        
        Returns:
            包含钱包信息的字典
        """
        balance = self.get_balance()
        domains = self.get_domains()
        
        return {
            "address": self.address,
            "balance": balance,
            "domains": domains
        }
    
    def get_balance(self) -> float:
        """
        获取钱包余额，从本地钱包文件查询
        
        Returns:
            钱包余额
        """
        wallet_file = os.path.join(self.data_dir, "wallet.json")
        try:
            with open(wallet_file, 'r') as f:
                wallets = json.load(f)
                # 遍历钱包列表查找匹配地址
                for wallet in wallets:
                    if wallet.get("address") == self.address:
                        return float(wallet.get("balance", 10.0))
                # 地址不存在时返回默认余额
                return 10.0
        except Exception as e:
            print(f"从本地钱包文件获取余额失败: {str(e)}")
            return 10.0  # 异常时返回默认余额
    def add_balance(self, amount: float):
        """
        为钱包添加余额，更新本地钱包文件

        Args:
            amount: 要添加的余额
        """
        wallet_file = os.path.join(self.data_dir, "wallet.json")
        try:
            with open(wallet_file, 'r') as f:
                wallets = json.load(f)
            # 遍历钱包列表查找匹配地址
            for wallet in wallets:
                if wallet.get("address") == self.address:
                    wallet["balance"] = float(wallet.get("balance", 0.0)) + amount
                    break
            else:
                # 地址不存在时新增
                wallets.append({
                    "address": self.address,
                    "balance": amount
                })
            # 保存钱包文件
            with open(wallet_file, 'w') as f:
                json.dump(wallets, f, indent=2)
        except Exception as e:
            print(f"更新本地钱包文件失败: {str(e)}")

    def get_domains(self) -> List[Dict]:
        """
        获取钱包拥有的域名列表，从区块链上查询
        
        Returns:
            域名列表，每个域名是一个字典
        """
        # 从区块链上查询域名
        try:
            # 初始化DNS解析器以获取区块链实例
            dns_resolver = dns_layer(node_identifier=self.node_identifier)
            
            # 获取注册链和DNS链
            register_chain = dns_resolver.register_blockchain.chain
            dns_chain = dns_resolver.dns_blockchain.chain
            
            # 查找该钱包地址拥有的所有域名
            domains = []
            
            # 从注册链中查找域名
            for block in register_chain:
                for tx in block['transactions']:
                    if tx.get('type') == 'domain_register' and tx.get('wallet') == self.address:
                        # 找到该钱包注册的域名
                        domain = {
                            "hostname": tx.get('hostname'),
                            "owner": self.address,
                            "blockchain_type": "注册链",
                            "lease_expiry": tx.get('lease_expiry', int(time.time()) + 31536000)  # 默认一年后过期
                        }
                        
                        # 从DNS链中查找该域名的IP和端口
                        for dns_block in dns_chain:
                            for dns_tx in dns_block['transactions']:
                                if dns_tx.get('hostname') == domain["hostname"]:
                                    domain["ip"] = dns_tx.get('ip')
                                    domain["port"] = dns_tx.get('port')
                                    break
                        
                        domains.append(domain)
            
            if domains:
                return domains
        except Exception as e:
            print(f"从区块链获取域名失败: {str(e)}")
        
        # 如果从区块链查询失败或没有域名，尝试从本地文件获取
        domains_file = os.path.join(self.data_dir, "domains.json")
        
        if os.path.exists(domains_file):
            try:
                with open(domains_file, 'r') as f:
                    all_domains = json.load(f)
                    # 筛选当前地址拥有的域名
                    return [domain for domain in all_domains 
                            if domain.get("owner") == self.address]
            except Exception:
                pass
                
        # 如果没有数据或出错，返回空列表
        # 这里可以添加一些模拟数据用于演示
        current_time = int(time.time())
        # 三个月后过期
        expiry = current_time + 90 * 24 * 60 * 60
        
        sample_domains = [
            {
                "hostname": "example.dc",
                "owner": self.address,
                "ip": "192.168.1.1",
                "port": 80,
                "blockchain_type": "注册链",
                "lease_expiry": expiry
            }
        ]
        
        # 保存示例数据
        self._save_sample_data(sample_domains)
        
        return sample_domains
        
    def _save_sample_data(self, domains: List[Dict]):
        """保存示例数据到文件"""
        domains_file = os.path.join(self.data_dir, "domains.json")
        
        try:
            with open(domains_file, 'w') as f:
                json.dump(domains, f, indent=2)
                
            # 设置余额
            balance_file = os.path.join(self.data_dir, "balances.json")
            balances = {self.address: 10.0}
            
            with open(balance_file, 'w') as f:
                json.dump(balances, f, indent=2)
        except Exception as e:
            print(f"保存示例数据时出错: {str(e)}")
    
    def sign_message(self, message: str) -> str:
        """
        使用私钥签名消息
        
        Args:
            message: 要签名的消息
            
        Returns:
            签名的十六进制字符串
        """
        sk = ecdsa.SigningKey.from_string(
            binascii.unhexlify(self.private_key),
            curve=ecdsa.SECP256k1
        )
        signature = sk.sign(message.encode())
        return binascii.hexlify(signature).decode('utf-8')
    
    def verify_signature(self, message: str, signature: str) -> bool:
        """
        验证签名
        
        Args:
            message: 原始消息
            signature: 签名
            
        Returns:
            验证结果，True为有效签名
        """
        vk = ecdsa.VerifyingKey.from_string(
            binascii.unhexlify(self.public_key),
            curve=ecdsa.SECP256k1
        )
        try:
            return vk.verify(
                binascii.unhexlify(signature),
                message.encode()
            )
        except ecdsa.BadSignatureError:
            return False
    
    @staticmethod
    def validate_address(address: str) -> bool:
        """
        验证地址是否有效
        
        Args:
            address: 要验证的地址
            
        Returns:
            地址是否有效
        """
        # 简单的验证规则，实际应用中可能需要更复杂的验证
        return address.startswith('DC') and len(address) == 42