<script setup lang="ts">
import { ref } from 'vue';

// 定义状态变量
const activeTab = ref('register');
const hostname = ref('');
const ip = ref('');
const port = ref('');
const leaseYears = ref(1);
const message = ref('');
const error = ref('');

// 切换标签页
function setActiveTab(tab) {
  activeTab.value = tab;
  message.value = '';
  error.value = '';
}

// 注册域名（需要代币和租赁）
async function registerDomain() {
  try {
    error.value = '';
    message.value = '';
    
    if (!hostname.value || !ip.value || !port.value) {
      error.value = '请填写所有必填字段';
      return;
    }
    
    const response = await fetch('/dns/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        hostname: hostname.value,
        ip: ip.value,
        port: port.value,
        lease_years: leaseYears.value
      })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      message.value = data.message;
      // 清空表单
      hostname.value = '';
      ip.value = '';
      port.value = '';
    } else {
      error.value = data.error || '注册失败';
    }
  } catch (err) {
    error.value = '请求出错，请稍后再试';
    console.error(err);
  }
}

// 添加DNS记录（不需要代币和租赁）
async function addDnsRecord() {
  try {
    error.value = '';
    message.value = '';
    
    if (!hostname.value || !ip.value || !port.value) {
      error.value = '请填写所有必填字段';
      return;
    }
    
    const response = await fetch('/dns/new', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        'entry': {
          hostname: hostname.value,
          ip: ip.value,
          port: port.value
        }
      })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      message.value = data.message;
      // 清空表单
      hostname.value = '';
      ip.value = '';
      port.value = '';
    } else {
      error.value = data.error || '添加记录失败';
    }
  } catch (err) {
    error.value = '请求出错，请稍后再试';
    console.error(err);
  }
}
</script>

<template>
  <div class="register-view">
    <h1>DNS管理</h1>
    
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
              placeholder="192.168.1.1"
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

input {
  width: 100%;
  padding: 8px;
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