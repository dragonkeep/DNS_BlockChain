<script setup lang="ts">
import { ref } from 'vue';

// 定义类型
interface QueryResult {
  hostname?: string;
  ip?: string;
  port?: string | number;
  lease_expiry?: number;
  blockchain_type?: string;
  on_chain?: boolean;
  message?: string;
}

// 定义状态变量
const hostname = ref('');
const queryResult = ref<QueryResult | null>(null);
const error = ref('');

// 查询域名信息
async function queryDomain() {
  try {
    error.value = '';
    queryResult.value = null;
    
    if (!hostname.value) {
      error.value = '请输入要查询的域名';
      return;
    }
    
    // 适配后端接口
    const response = await fetch('/dns/request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hostname: hostname.value })
    });
    const data = await response.json();
    
    if (response.ok) {
      queryResult.value = { ...data, hostname: hostname.value };
    } else {
      error.value = data.error || '查询失败';
    }
  } catch (err) {
    error.value = '请求出错，请稍后再试';
    console.error(err);
  }
}
</script>

<template>
  <div class="dns-view">
    <h1>DNS解析</h1>
    <div class="query-form">
      <h2>域名查询</h2>
      <form @submit.prevent="queryDomain">
        <div class="form-group">
          <label for="hostname-query">域名:</label>
          <input 
            type="text" 
            id="hostname-query" 
            v-model="hostname" 
            placeholder="example.com"
            required
          >
        </div>
        <button type="submit" class="btn-primary">查询</button>
      </form>
      <div v-if="queryResult" class="result">
        <h3>查询结果:</h3>
        <div class="result-item">
          <strong>域名:</strong> {{ queryResult.hostname }}
        </div>
        <div class="result-item">
          <strong>IP地址:</strong> {{ queryResult.ip }}
        </div>
        <div class="result-item">
          <strong>端口:</strong> {{ queryResult.port }}
        </div>
        <div class="result-item" v-if="queryResult.lease_expiry">
          <strong>租约到期时间:</strong> {{ new Date(queryResult.lease_expiry * 1000).toLocaleString() }}
        </div>
        <div class="result-item" v-if="queryResult.blockchain_type">
          <strong>区块链类型:</strong> {{ queryResult.blockchain_type }}
        </div>
        <div v-if="queryResult && (queryResult.on_chain === false || queryResult.on_chain === 'false')">
          <strong style="color: #e67e22">[未上链]</strong>
          <span>{{ queryResult.message || '该DNS记录未上链' }}</span>
        </div>
        <div v-else-if="queryResult && queryResult.error">
          <span style="color: #e74c3c">{{ queryResult.error }}</span>
        </div>
      </div>
      <div v-if="error" class="message error">{{ error }}</div>
    </div>
  </div>
</template>

<style scoped>
.dns-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;

}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
}

.query-form {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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

.result {
  margin-top: 20px;
  padding: 15px;
  background-color: #f0f8ff;
  border-radius: 4px;
  border: 1px solid #b8daff;
}

.result-item {
  margin-bottom: 10px;
  font-size: 16px;
}

.message {
  padding: 10px;
  margin-top: 20px;
  border-radius: 4px;
}

.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
</style>