<script setup lang="ts">
import { ref } from 'vue';
import { RouterLink, RouterView, useRouter } from 'vue-router';
import UserAuth from './components/UserAuth.vue';
import { walletService } from './services/walletService';

// 定义状态变量
const message = ref('');
const error = ref('');

// 清除提示信息
function clearMessage() {
  setTimeout(() => {
    message.value = '';
    error.value = '';
  }, 2000);
}

// 处理登录成功
const onLoginSuccess = () => {
  // 登录成功后强制刷新整个页面，确保所有状态和数据都更新
  window.location.href = '/wallet';
};

// 处理登出
const onLogout = () => {
  // 退出登录后强制刷新页面并跳转到首页
  window.location.href = '/';
};

// 处理钱包绑定事件
const handleWalletBind = (walletAddress: string) => {
  message.value = `钱包已绑定: ${walletAddress}`;
  clearMessage();
};

// 处理钱包解绑事件
const handleWalletUnbind = async () => {
  try {
    // 调用钱包服务清除钱包信息
    await walletService.clearWalletInfo();
    
    // 清除本地存储的钱包信息
    localStorage.removeItem('walletAddress');
    message.value = '钱包已解绑';
    clearMessage();
  } catch (err) {
    error.value = '钱包解绑失败';
    clearMessage();
    console.error('钱包解绑失败:', err);
    
    // 即使API调用失败，也尝试清除本地存储
    localStorage.removeItem('walletAddress');
  }
};

const router = useRouter();

// 登录成功处理函数
// function onLoginSuccess() {
//   // 登录成功后刷新当前页面或跳转到钱包管理
//   router.push('/wallet');
// }
</script>

<template>
  <div class="container">
    <header class="header">
      <div class="header-content">
        <h1>区块链DNS系统</h1>
        <UserAuth
          @wallet-bind="handleWalletBind"
          @wallet-unbind="handleWalletUnbind"
          @login-success="onLoginSuccess"
          @logout="onLogout"
        />
      </div>
      
      <nav class="main-nav">
        <RouterLink to="/" class="nav-link">首页</RouterLink>
        <RouterLink to="/register" class="nav-link">域名管理</RouterLink>
        <RouterLink to="/dns" class="nav-link">域名查询</RouterLink>
        <RouterLink to="/blockchain" class="nav-link">区块链状态</RouterLink>
        <RouterLink to="/wallet" class="nav-link">钱包管理</RouterLink>
        <RouterLink to="/about" class="nav-link">关于</RouterLink>
      </nav>
    </header>
    
    <main class="main-content">
      <RouterView />
    </main>
    
    <div v-if="message" class="message success">{{ message }}</div>
    <div v-if="error" class="message error">{{ error }}</div>
    
    <footer class="footer">
      <p>© 2025 区块链DNS系统 - 基于区块链技术的分布式域名系统</p>
    </footer>
  </div>
</template>

<style>
.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #ffffff;
  color: #333333;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.header {
  margin-bottom: 20px;
  border-bottom: 1px solid #eaeaea;
  padding-bottom: 15px;
}

.header-content {
  position: relative;
  padding: 0 20px;
}

h1 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 20px;
  font-weight: 600;
}

.main-nav {
  display: flex;
  justify-content: center;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.nav-link {
  padding: 10px 20px;
  margin: 0 5px;
  color: #2c3e50;
  text-decoration: none;
  border-radius: 4px;
  transition: all 0.3s ease;
  font-weight: 500;
}

.nav-link:hover {
  background-color: #f0f0f0;
}

.router-link-active {
  color: #42b983;
  font-weight: bold;
  border-bottom: 2px solid #42b983;
}

.main-content {
  flex: 1;
  margin-bottom: 30px;
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

.btn-secondary {
  background-color: #2c3e50;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.message {
  padding: 12px 15px;
  margin-top: 20px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  animation: fadeIn 0.5s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.success {
  background-color: #d4edda;
  color: #155724;
  border-left: 4px solid #28a745;
}

.error {
  background-color: #f8d7da;
  color: #721c24;
  border-left: 4px solid #dc3545;
}

.footer {
  margin-top: auto;
  text-align: center;
  padding: 15px 0;
  color: #6c757d;
  font-size: 0.9rem;
  border-top: 1px solid #eaeaea;
}

.result {
  margin-top: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #ddd;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  font-size: 14px;
}
</style>