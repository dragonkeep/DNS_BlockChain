<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { mockApi } from '../services/mockApi';

// 获取路由参数
const route = useRoute();

// 定义状态变量
const activeTab = ref('register');
const hostname = ref('');
const ip = ref('');
const port = ref('');
const leaseYears = ref(1);
const message = ref('');
const error = ref('');
const recordType = ref('A');
const recordValue = ref('');
const walletAddress = ref('');
const isWalletConnected = ref(false);

// DNS记录类型选项
const recordTypes = [
  { value: 'CNAME', label: 'CNAME (别名)' },
  { value: 'MX', label: 'MX (邮件服务器)' },
  { value: 'NS', label: 'NS (域名服务器)' },
  { value: 'TXT', label: 'TXT (文本记录)' },
  { value: 'SOA', label: 'SOA (起始授权)' }
];

// 根据记录类型获取值的占位符
function getValuePlaceholder(type: string) {
  switch(type) {
    case 'CNAME': return 'alias.example.com';
    case 'MX': return 'mx.example.com';
    case 'NS': return 'ns.example.com';
    case 'TXT': return '文本记录内容';
    case 'SOA': return 'ns1.example.com admin.example.com';
    default: return '';
  }
}

// 根据记录类型获取值的标签
function getValueLabel(type: string) {
  switch(type) {
    case 'CNAME': return '别名';
    case 'MX': return '邮件服务器';
    case 'NS': return '域名服务器';
    case 'TXT': return '文本内容';
    case 'SOA': return 'SOA记录';
    default: return '记录值';
  }
}

// 切换标签页
function setActiveTab(tab:any) {
  activeTab.value = tab;
  message.value = '';
  error.value = '';
}

// 检查钱包连接状态
function checkWalletConnection() {
  const savedAddress = localStorage.getItem('walletAddress');
  if (savedAddress) {
    walletAddress.value = savedAddress;
    isWalletConnected.value = true;
    return true;
  }
  return false;
}

// 注册域名（需要代币和租赁）- 使用mockApi
async function registerDomain() {
  try {
    error.value = '';
    message.value = '';
    
    if (!hostname.value || !ip.value || !port.value) {
      error.value = '请填写所有必填字段';
      return;
    }
    
    // 检查钱包是否已连接
    if (!checkWalletConnection()) {
      error.value = '请先连接钱包';
      return;
    }
    
    const result = await mockApi.registerDomain({
      hostname: hostname.value,
      ip: ip.value,
      port: port.value,
      lease_years: leaseYears.value,
      wallet_address: walletAddress.value
    });
    
    message.value = result.message;
    // 清空表单
    hostname.value = '';
    ip.value = '';
    port.value = '';
  } catch (err: any) {
    error.value = err.message || '注册失败';
    console.error(err);
  }
}

// 添加DNS记录（不需要代币和租赁）- 使用mockApi
async function addDnsRecord() {
  try {
    error.value = '';
    message.value = '';
    
    if (!hostname.value || !ip.value || !port.value) {
      error.value = '请填写所有必填字段';
      return;
    }
    
    // 检查钱包是否已连接
    if (!checkWalletConnection()) {
      error.value = '请先连接钱包';
      return;
    }
    
    let value = recordValue.value;
    if (recordType.value === 'MX') {
      // MX记录需要包含优先级
      value = [recordValue.value, 10]; // 默认优先级为10
    } else if (recordType.value === 'SOA') {
      // SOA记录需要包含主域名服务器和管理员邮箱
      value = recordValue.value.split(' ');
    }
    
    const result = await mockApi.addDnsRecord({
      entry: {
        hostname: hostname.value,
        type: recordType.value,
        value: value,
        ip: ip.value,
        port: port.value,
        wallet_address: walletAddress.value
      }
    });
    
    message.value = result.message;
    // 清空表单
    hostname.value = '';
    recordValue.value = '';
    ip.value = '';
    port.value = '';
  } catch (err: any) {
    error.value = err.message || '添加记录失败';
    console.error(err);
  }
}

// 页面加载时检查钱包连接状态和预填充域名
onMounted(() => {
  // 检查钱包连接状态
  checkWalletConnection();
  
  // 检查URL参数是否有编辑域名
  const editDomain = route.query.edit;
  if (editDomain && typeof editDomain === 'string') {
    hostname.value = editDomain;
    activeTab.value = 'add'; // 切换到添加DNS记录标签页
  }
});
</script>

<template>
  <div class="register-view">
    <h1>DNS管理</h1>
    
    <!-- 钱包连接状态 -->
    <div class="wallet-status">
      <template v-if="isWalletConnected">
        <div class="wallet-connected">
          <span class="status-icon">✓</span>
          钱包已连接: <span class="wallet-address">{{ walletAddress.substring(0, 8) }}...{{ walletAddress.substring(walletAddress.length - 4) }}</span>
        </div>
      </template>
      <template v-else>
        <div class="wallet-disconnected">
          <span class="status-icon">✗</span>
          钱包未连接
          <RouterLink to="/wallet" class="btn-connect">连接钱包</RouterLink>
        </div>
      </template>
    </div>
    
    <div class="tabs">
      <button 
        :class="{ active: activeTab === 'register' }" 
        @click="setActiveTab('register')"
      >
        域名注册
      </button>
      <button 
        :class="{ active: activeTab === 'add' }" 
        @click="setActiveTab('add')"
      >
        添加DNS记录
      </button>
    </div>
    
    <div class="content">
      <!-- 域名注册表单 -->
      <div v-if="activeTab === 'register'" class="tab-content">
        <h2>域名注册</h2>
        <form @submit.prevent="registerDomain">
          <div class="form-group">
            <label for="hostname">域名:</label>
            <input 
              type="text" 
              id="hostname" 
              v-model="hostname" 
              placeholder="localhost"
              required
            >
          </div>
          
          <div class="form-group">
            <label for="ip">IP地址:</label>
            <input 
              type="text" 
              id="ip" 
              v-model="ip" 
              placeholder="127.0.0.1"
              required
            >
          </div>
          
          <div class="form-group">
            <label for="port">端口:</label>
            <input 
              type="number" 
              id="port" 
              v-model="port" 
              placeholder="80"
              required
            >
          </div>
          
          <div class="form-group">
            <label for="lease">租赁年限:</label>
            <input 
              type="number" 
              id="lease" 
              v-model="leaseYears" 
              min="1"
              required
            >
          </div>
          
          <button type="submit" class="btn-primary">注册域名</button>
        </form>
      </div>
      
      <!-- 添加DNS记录表单 -->
      <div v-if="activeTab === 'add'" class="tab-content">
        <h2>添加DNS记录</h2>
        <form @submit.prevent="addDnsRecord">
          <div class="form-group">
            <label for="hostname-add">域名:</label>
            <input 
              type="text" 
              id="hostname-add" 
              v-model="hostname" 
              placeholder="example.com"
              required
            >
          </div>
          
          <div class="form-group">
            <label for="ip-add">IP地址:</label>
            <input 
              type="text" 
              id="ip-add" 
              v-model="ip" 
              placeholder="127.0.0.1"
              required
            >
          </div>
          
          <div class="form-group">
            <label for="port-add">端口:</label>
            <input 
              type="number" 
              id="port-add" 
              v-model="port" 
              placeholder="80"
              required
            >
          </div>
          
          <div class="form-group">
            <label for="record-type">记录类型:</label>
            <select 
              id="record-type" 
              v-model="recordType"
              
            >
              <option v-for="type in recordTypes" :key="type.value" :value="type.value">
                {{ type.label }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="record-value">{{ getValueLabel(recordType) }}:</label>
            <input 
              type="text" 
              id="record-value" 
              v-model="recordValue" 
              :placeholder="getValuePlaceholder(recordType)"
              
            >
          </div>
          
          <button type="submit" class="btn-primary">添加记录</button>
        </form>
      </div>
      
      <!-- 消息提示 -->
      <div v-if="message" class="message success">{{ message }}</div>
      <div v-if="error" class="message error">{{ error }}</div>
    </div>
  </div>
</template>



<style scoped>
.register-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.wallet-status {
  background-color: #f9f9f9;
  padding: 10px 15px;
  border-radius: 6px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.wallet-connected {
  color: #27ae60;
  display: flex;
  align-items: center;
}

.wallet-disconnected {
  color: #e74c3c;
  display: flex;
  align-items: center;
}

.status-icon {
  font-size: 18px;
  margin-right: 8px;
}

.wallet-address {
  font-family: monospace;
  background-color: #f0f0f0;
  padding: 4px 8px;
  border-radius: 4px;
  margin-left: 8px;
}

.btn-connect {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  margin-left: 10px;
  text-decoration: none;
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

.tab-content {
  padding: 20px 0;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

select {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: #fff;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 16px;
  transition: all 0.3s ease;
  cursor: pointer;
}

select:hover {
  border-color: #42b983;
}

select:focus {
  outline: none;
  border-color: #42b983;
  box-shadow: 0 0 0 2px rgba(66, 185, 131, 0.2);
}

option {
  padding: 10px;
}

option:hover {
  background-color: #f0f9f5;
}

.btn-primary {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
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
</style>