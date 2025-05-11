<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { walletService } from '../services/walletService';

// 定义状态变量
const activeTab = ref('create');
const walletAddress = ref('');
const privateKey = ref('');
const walletBalance = ref(0);
const ownedDomains = ref([]);
const message = ref('');
const error = ref('');
const showPrivateKey = ref(false);
const isWalletLoaded = ref(false);
const isLoading = ref(false);

// 切换标签页
function setActiveTab(tab:any) {
  activeTab.value = tab;
  message.value = '';
  error.value = '';
}

// 生成新钱包（调用后端API）
async function createWallet() {
  try {
    error.value = '';
    message.value = '';
    isLoading.value = true;
    
    const data = await walletService.createWallet();
    
    walletAddress.value = data.address;
    privateKey.value = data.private_key;
    message.value = '钱包创建成功！';
    isWalletLoaded.value = true;
    
    // 保存钱包地址到本地存储
    localStorage.setItem('walletAddress', walletAddress.value);
    
    // 获取钱包信息
    getWalletInfo();
  } catch (err) {
    error.value = err instanceof Error ? err.message : '创建钱包失败';
    console.error(err);
  } finally {
    isLoading.value = false;
  }
}

// 导入现有钱包
async function importWallet() {
  try {
    error.value = '';
    message.value = '';
    
    if (!privateKey.value) {
      error.value = '请输入私钥';
      return;
    }
    
    isLoading.value = true;
    
    const data = await walletService.importWallet(privateKey.value);
    
    walletAddress.value = data.address;
    message.value = '钱包导入成功！';
    isWalletLoaded.value = true;
    
    // 保存钱包地址到本地存储
    localStorage.setItem('walletAddress', walletAddress.value);
    
    // 获取钱包信息
    getWalletInfo();
  } catch (err) {
    error.value = err instanceof Error ? err.message : '导入钱包失败';
    console.error(err);
  } finally {
    isLoading.value = false;
  }
}

// 获取钱包信息（余额和域名）
async function getWalletInfo() {
  try {
    if (!walletAddress.value) {
      return;
    }
    
    isLoading.value = true;
    
    const data = await walletService.getWalletInfo(walletAddress.value);
    
    walletBalance.value = data.balance;
    ownedDomains.value = data.domains || [];
  } catch (err) {
    console.error('获取钱包信息失败:', err);
    error.value = err instanceof Error ? err.message : '获取钱包信息失败';
  } finally {
    isLoading.value = false;
  }
}

// 注册新域名（示例功能）
async function registerDomain(domainName: string, ip: string, port: number) {
  try {
    if (!walletAddress.value || !domainName || !ip) {
      error.value = '缺少必要参数';
      return;
    }
    
    isLoading.value = true;
    
    const response = await fetch(`${API_BASE_URL}/domain/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        hostname: domainName,
        owner: walletAddress.value,
        ip: ip,
        port: port || 80,
        blockchain_type: '注册链'
      })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      message.value = '域名注册成功！';
      // 重新获取钱包信息以更新域名列表
      getWalletInfo();
    } else {
      error.value = data.error || '域名注册失败';
    }
  } catch (err) {
    error.value = '请求出错，请稍后再试';
    console.error(err);
  } finally {
    isLoading.value = false;
  }
}

// 切换显示/隐藏私钥
function toggleShowPrivateKey() {
  showPrivateKey.value = !showPrivateKey.value;
}

// 格式化租赁到期时间
function formatLeaseExpiry(timestamp:any) {
  const date = new Date(timestamp * 1000);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

// 计算剩余租赁时间（天数）
function getRemainingDays(timestamp:any) {
  const now = Math.floor(Date.now() / 1000);
  const remainingSeconds = timestamp - now;
  return Math.max(0, Math.floor(remainingSeconds / 86400)); // 86400秒 = 1天
}

// 页面加载时检查是否有保存的钱包地址
onMounted(() => {
  const savedAddress = localStorage.getItem('walletAddress');
  if (savedAddress) {
    walletAddress.value = savedAddress;
    isWalletLoaded.value = true;
    getWalletInfo();
  }
});

// 保存钱包地址到本地存储
function saveWalletAddress() {
  if (walletAddress.value) {
    localStorage.setItem('walletAddress', walletAddress.value);
    message.value = '钱包地址已保存';
  }
}

// 清除保存的钱包信息
function clearWalletInfo() {
  localStorage.removeItem('walletAddress');
  walletAddress.value = '';
  privateKey.value = '';
  walletBalance.value = 0;
  ownedDomains.value = [];
  isWalletLoaded.value = false;
  message.value = '钱包信息已清除';
}

// 注册新域名变量和函数
const showRegisterForm = ref(false);
const newDomainName = ref('');
const newDomainIP = ref('');
const newDomainPort = ref(80);

function toggleRegisterForm() {
  showRegisterForm.value = !showRegisterForm.value;
  if (!showRegisterForm.value) {
    // 重置表单
    newDomainName.value = '';
    newDomainIP.value = '';
    newDomainPort.value = 80;
  }
}

function submitRegisterDomain() {
  if (!newDomainName.value || !newDomainIP.value) {
    error.value = '请填写域名和IP地址';
    return;
  }
  
  registerDomain(newDomainName.value, newDomainIP.value, newDomainPort.value);
  toggleRegisterForm();
}
</script>

<!-- 保留现有的模板部分 -->
<template>
  <div class="wallet-view">
    <h1>区块链钱包管理</h1>
    
    <div class="tabs">
      <button 
        :class="{ active: activeTab === 'create' }" 
        @click="setActiveTab('create')"
      >
        创建/导入钱包
      </button>
      <button 
        :class="{ active: activeTab === 'info' }" 
        @click="setActiveTab('info')"
        :disabled="!isWalletLoaded"
      >
        钱包信息
      </button>
      <button 
        :class="{ active: activeTab === 'domains' }" 
        @click="setActiveTab('domains')"
        :disabled="!isWalletLoaded"
      >
        子域名管理
      </button>
    </div>
    
    <div class="content">
      <!-- 加载指示器 -->
      <div v-if="isLoading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <p>请稍候...</p>
      </div>
      
      <!-- 创建/导入钱包 -->
      <div v-if="activeTab === 'create'" class="tab-content">
        <div v-if="!isWalletLoaded">
          <h2>创建新钱包</h2>
          <p class="description">创建一个新的钱包地址，用于管理您的代币和域名。</p>
          <button @click="createWallet" class="btn-primary">创建钱包</button>
          
          <div class="divider">或者</div>
          
          <h2>导入现有钱包</h2>
          <p class="description">使用私钥导入您的现有钱包。</p>
          <div class="form-group">
            <label for="private-key">私钥:</label>
            <input 
              type="password" 
              id="private-key" 
              v-model="privateKey" 
              placeholder="输入您的私钥"
              required
            >
          </div>
          <button @click="importWallet" class="btn-primary">导入钱包</button>
        </div>
        
        <div v-else class="wallet-created">
          <h2>钱包信息</h2>
          <div class="info-item">
            <strong>钱包地址:</strong> 
            <div class="address-container">
              <span class="address">{{ walletAddress }}</span>
              <button @click="saveWalletAddress" class="btn-small">保存地址</button>
            </div>
          </div>
          
          <div v-if="privateKey" class="info-item">
            <strong>私钥:</strong> 
            <div class="private-key-container">
              <span v-if="showPrivateKey" class="private-key">{{ privateKey }}</span>
              <span v-else class="private-key-hidden">************************</span>
              <button @click="toggleShowPrivateKey" class="btn-small">
                {{ showPrivateKey ? '隐藏' : '显示' }}
              </button>
            </div>
            <p class="warning">警告：请妥善保管您的私钥，不要泄露给任何人！</p>
          </div>
          
          <button @click="clearWalletInfo" class="btn-danger">清除钱包信息</button>
        </div>
      </div>
      
      <!-- 钱包信息 -->
      <div v-if="activeTab === 'info'" class="tab-content">
        <h2>钱包详情</h2>
        
        <div class="wallet-info">
          <div class="info-card">
            <h3>钱包地址</h3>
            <p class="address">{{ walletAddress }}</p>
          </div>
          
          <div class="info-card">
            <h3>余额</h3>
            <p class="balance">{{ walletBalance }} <span class="token-name">DC</span></p>
          </div>
          
          <div class="info-card">
            <h3>拥有域名数量</h3>
            <p class="domain-count">{{ ownedDomains.length }}</p>
          </div>
        </div>
        
        <button @click="getWalletInfo" class="btn-refresh">刷新信息</button>
      </div>
      
      <!-- 域名管理 -->
      <div v-if="activeTab === 'domains'" class="tab-content">
        <div class="domains-header">
          <h2>我的域名</h2>
          <button @click="toggleRegisterForm" class="btn-primary">
            {{ showRegisterForm ? '取消' : '注册新域名' }}
          </button>
        </div>
        
        <!-- 注册域名表单 -->
        <div v-if="showRegisterForm" class="register-form">
          <h3>注册新域名</h3>
          <div class="form-group">
            <label for="domain-name">域名:</label>
            <input 
              type="text" 
              id="domain-name" 
              v-model="newDomainName" 
              placeholder="example.dc"
              required
            >
          </div>
          
          <div class="form-group">
            <label for="domain-ip">IP地址:</label>
            <input 
              type="text" 
              id="domain-ip" 
              v-model="newDomainIP" 
              placeholder="192.168.1.1"
              required
            >
          </div>
          
          <div class="form-group">
            <label for="domain-port">端口:</label>
            <input 
              type="number" 
              id="domain-port" 
              v-model="newDomainPort" 
              min="1"
              max="65535"
            >
          </div>
          
          <button @click="submitRegisterDomain" class="btn-primary">提交注册</button>
        </div>
        
        <div v-if="ownedDomains.length === 0 && !showRegisterForm" class="no-domains">
          <p>您还没有注册任何域名</p>
        </div>
        
        <div v-else-if="ownedDomains.length > 0" class="domains-list">
          <div v-for="(domain, index) in ownedDomains" :key="index" class="domain-item">
            <div class="domain-header">
              <h3>{{ domain.hostname }}</h3>
              <span class="domain-type" :class="domain.blockchain_type === '注册链' ? 'premium' : 'standard'">
                {{ domain.blockchain_type === '注册链' ? '高级域名' : '标准域名' }}
              </span>
            </div>
            
            <div class="domain-details">
              <div class="detail-item">
                <strong>IP地址:</strong> {{ domain.ip }}
              </div>
              <div class="detail-item">
                <strong>端口:</strong> {{ domain.port }}
              </div>
              <div v-if="domain.lease_expiry" class="detail-item">
                <strong>租赁到期:</strong> {{ formatLeaseExpiry(domain.lease_expiry) }}
                <span class="remaining-days" :class="getRemainingDays(domain.lease_expiry) < 30 ? 'expiring' : ''">
                  (剩余 {{ getRemainingDays(domain.lease_expiry) }} 天)
                </span>
              </div>
            </div>
            
            <div class="domain-actions">
              <button class="btn-small">管理DNS记录</button>
              <button v-if="domain.blockchain_type === '注册链' && getRemainingDays(domain.lease_expiry) < 90" class="btn-small btn-renew">续租域名</button>
            </div>
          </div>
        </div>
        
        <button @click="getWalletInfo" class="btn-refresh">刷新域名列表</button>
      </div>
      
      <!-- 消息提示 -->
      <div v-if="message" class="message success">{{ message }}</div>
      <div v-if="error" class="message error">{{ error }}</div>
    </div>
  </div>
</template>

<style scoped>
.wallet-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
}

.tabs {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 1px solid #ddd;
}

.tabs button {
  padding: 10px 20px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: #666;
}

.tabs button.active {
  color: #2c3e50;
  border-bottom: 2px solid #42b983;
  font-weight: bold;
}

.tabs button:disabled {
  color: #ccc;
  cursor: not-allowed;
}

.tab-content {
  padding: 20px 0;
  position: relative;
}

.description {
  color: #666;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.btn-primary {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin-top: 10px;
}

.btn-small {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  margin-left: 10px;
}

.btn-danger {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin-top: 20px;
}

.btn-refresh {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin-top: 20px;
}

.btn-renew {
  background-color: #f39c12;
}

.divider {
  text-align: center;
  margin: 30px 0;
  color: #999;
  position: relative;
}

.divider::before,
.divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 45%;
  height: 1px;
  background-color: #ddd;
}

.divider::before {
  left: 0;
}

.divider::after {
  right: 0;
}

.wallet-created {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #eee;
}

.info-item {
  margin-bottom: 15px;
}

.address-container,
.private-key-container {
  display: flex;
  align-items: center;
  margin-top: 5px;
}

.address,
.private-key {
  font-family: monospace;
  background-color: #f0f0f0;
  padding: 8px;
  border-radius: 4px;
  word-break: break-all;
  flex: 1;
}

.private-key-hidden {
  font-family: monospace;
  background-color: #f0f0f0;
  padding: 8px;
  border-radius: 4px;
  flex: 1;
}

.warning {
  color: #e74c3c;
  font-size: 14px;
  margin-top: 5px;
}

.wallet-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.info-card {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.info-card h3 {
  margin-top: 0;
  color: #666;
  font-size: 16px;
}

.balance {
  font-size: 24px;
  font-weight: bold;
  color: #42b983;
  margin: 10px 0 0;
}

.token-name {
  font-size: 14px;
  color: #666;
}

.address {
  font-size: 14px;
  word-break: break-all;
}

.domain-count {
  font-size: 24px;
  font-weight: bold;
  color: #3498db;
  margin: 10px 0 0;
}

.no-domains {
  text-align: center;
  padding: 30px;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.domains-list {
  display: grid;
  gap: 20px;
}

.domains-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.register-form {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid #eee;
}

.domain-item {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.domain-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.domain-header h3 {
  margin: 0;
  color: #2c3e50;
}

.domain-type {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 12px;
  font-weight: bold;
}

.domain-type.premium {
  background-color: #f1c40f;
  color: #7d6608;
}

.domain-type.standard {
  background-color: #3498db;
  color: #fff;
}

.domain-details {
  margin-bottom: 15px;
}

.detail-item {
  margin-bottom: 8px;
}

.remaining-days {
  margin-left: 5px;
  font-size: 14px;
  color: #27ae60;
}

.remaining-days.expiring {
  color: #e74c3c;
}

.domain-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 15px;
}

.message {
  padding: 10px;
  margin-top: 20px;
  border-radius: 4px;
}

.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 10;
  border-radius: 8px;
}

.loading-spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #42b983;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>