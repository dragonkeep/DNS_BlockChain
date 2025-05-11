<script setup lang="ts">
import { ref, onMounted } from 'vue';

// 定义状态变量
const blockchainStatus = ref(null);
const registerBlockchainStatus = ref(null);
const loading = ref(false);
const error = ref('');

// 获取区块链状态
async function getBlockchainStatus() {
  try {
    loading.value = true;
    error.value = '';
    
    // 获取DNS区块链状态
    const dnsResponse = await fetch('/nodes/chain?type=dns');
    const dnsData = await dnsResponse.json();
    
    if (dnsResponse.ok) {
      blockchainStatus.value = dnsData;
    }
    
    // 获取注册区块链状态
    const registerResponse = await fetch('/nodes/chain?type=register');
    const registerData = await registerResponse.json();
    
    if (registerResponse.ok) {
      registerBlockchainStatus.value = registerData;
    }
  } catch (err) {
    error.value = '获取区块链状态失败';
    console.error('获取区块链状态失败:', err);
  } finally {
    loading.value = false;
  }
}

// 页面加载时获取区块链状态
onMounted(() => {
  getBlockchainStatus();
});
</script>

<template>
  <div class="blockchain-view">
    <h1>区块链状态</h1>
    
    <button @click="getBlockchainStatus" class="btn-refresh" :disabled="loading">
      {{ loading ? '加载中...' : '刷新状态' }}
    </button>
    
    <div v-if="error" class="message error">{{ error }}</div>
    
    <div class="blockchain-container">
      <!-- DNS区块链状态 -->
      <div class="blockchain-section" v-if="blockchainStatus">
        <h2>DNS区块链</h2>
        
        <div class="blockchain-info">
          <div class="info-item">
            <strong>链长度:</strong> {{ blockchainStatus.length }}
          </div>
          
          <div class="info-item" v-if="blockchainStatus.current_transactions">
            <strong>当前交易数:</strong> {{ blockchainStatus.current_transactions.length }}
          </div>
          
          <h3>最新区块:</h3>
          <div class="block-info" v-if="blockchainStatus.chain && blockchainStatus.chain.length > 0">
            <div class="info-item">
              <strong>索引:</strong> {{ blockchainStatus.chain[blockchainStatus.chain.length - 1].index }}
            </div>
            <div class="info-item">
              <strong>时间戳:</strong> {{ new Date(blockchainStatus.chain[blockchainStatus.chain.length - 1].timestamp * 1000).toLocaleString() }}
            </div>
            <div class="info-item">
              <strong>交易数:</strong> {{ blockchainStatus.chain[blockchainStatus.chain.length - 1].transactions.length }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- 注册区块链状态 -->
      <div class="blockchain-section" v-if="registerBlockchainStatus">
        <h2>注册区块链</h2>
        
        <div class="blockchain-info">
          <div class="info-item">
            <strong>链长度:</strong> {{ registerBlockchainStatus.length }}
          </div>
          
          <div class="info-item" v-if="registerBlockchainStatus.current_transactions">
            <strong>当前交易数:</strong> {{ registerBlockchainStatus.current_transactions.length }}
          </div>
          
          <h3>最新区块:</h3>
          <div class="block-info" v-if="registerBlockchainStatus.chain && registerBlockchainStatus.chain.length > 0">
            <div class="info-item">
              <strong>索引:</strong> {{ registerBlockchainStatus.chain[registerBlockchainStatus.chain.length - 1].index }}
            </div>
            <div class="info-item">
              <strong>时间戳:</strong> {{ new Date(registerBlockchainStatus.chain[registerBlockchainStatus.chain.length - 1].timestamp * 1000).toLocaleString() }}
            </div>
            <div class="info-item">
              <strong>交易数:</strong> {{ registerBlockchainStatus.chain[registerBlockchainStatus.chain.length - 1].transactions.length }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.blockchain-view {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
}

.btn-refresh {
  background-color: #2c3e50;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin-bottom: 20px;
}

.btn-refresh:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.blockchain-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.blockchain-section {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.blockchain-info {
  margin-top: 15px;
}

.info-item {
  margin-bottom: 10px;
  font-size: 16px;
}

.block-info {
  background-color: #f0f8ff;
  padding: 15px;
  border-radius: 4px;
  margin-top: 10px;
  border: 1px solid #b8daff;
}

.message {
  padding: 10px;
  margin-bottom: 20px;
  border-radius: 4px;
}

.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

@media (min-width: 768px) {
  .blockchain-container {
    flex-direction: row;
  }
  
  .blockchain-section {
    flex: 1;
  }
}
</style>