<script setup lang="ts">
import { ref, onMounted } from 'vue';
import api from '../services/axios';

const showLogin = ref(true);
const showForm = ref(false);
const username = ref('');
const password = ref('');
const message = ref('');
const error = ref('');
const isLoggedIn = ref(false);
const currentUser = ref('');

const toggleForm = () => {
  showLogin.value = !showLogin.value;
  username.value = '';
  password.value = '';
  message.value = '';
  error.value = '';
};

const clearMessage = () => {
  setTimeout(() => {
    message.value = '';
    error.value = '';
  }, 2000);
};

const handleSubmit = async () => {
  try {
    const endpoint = showLogin.value ? '/user/login' : '/user/register';
    const response = await api.post(endpoint, {
      username: username.value,
      password: password.value
    });

    message.value = response.data.message;
    clearMessage(); // 添加自动清除消息
    
    if (showLogin.value) {
      isLoggedIn.value = true;
      currentUser.value = username.value;
      // 触发登录成功事件
      emit('login-success');
      
      // 如果有关联的钱包地址，自动绑定
      if (response.data.wallet_address) {
        // 触发钱包绑定事件
        emit('wallet-bind', response.data.wallet_address);
        // 保存钱包地址到本地存储
        localStorage.setItem('walletAddress', response.data.wallet_address);
      } else {
        // 如果没有关联的钱包地址，但本地存储有钱包地址，则自动绑定
        const savedWalletAddress = localStorage.getItem('walletAddress');
        if (savedWalletAddress) {
          try {
            // 调用API绑定钱包
            const bindResponse = await api.post('/user/bind-wallet', {
              wallet_address: savedWalletAddress
            });
            
            if (bindResponse.status === 200) {
              // 触发钱包绑定事件
              emit('wallet-bind', savedWalletAddress);
              message.value += ' 已自动绑定上次使用的钱包';
            }
          } catch (bindErr) {
            console.error('自动绑定钱包失败:', bindErr);
          }
        }
      }
    } else {
      // 注册成功后自动切换到登录表单
      setTimeout(() => {
        toggleForm();
      }, 1500);
    }
  } catch (err: any) {
    error.value = err.response?.data?.error || '操作失败';
  }
};

const logout = async () => {
  try {
    // 先解绑钱包
    try {
      await api.post('/user/unbind-wallet');
    } catch (unbindErr) {
      console.error('解绑钱包失败:', unbindErr);
      // 即使解绑失败，也继续退出登录
    }
    
    // 然后退出登录
    const response = await api.post('/user/logout');
    message.value = response.data.message;
    clearMessage(); // 添加自动清除消息
    isLoggedIn.value = false;
    currentUser.value = '';
    
    // 触发登出和钱包解绑事件
    emit('logout');
    emit('wallet-unbind');
  } catch (err: any) {
    error.value = err.response?.data?.error || '退出失败';
  }
};

// 定义事件
const emit = defineEmits(['wallet-bind', 'wallet-unbind', 'login-success', 'logout']);

// 检查登录状态
onMounted(async () => {
  try {
    const response = await api.get('/user/status');
    if (response.data.logged_in) {
      isLoggedIn.value = true;
      currentUser.value = response.data.username;
    }
  } catch (err) {
    console.error('检查登录状态失败:', err);
  }
});
</script>

<template>
  <div class="user-auth">
    <div v-if="!isLoggedIn">
      <button v-if="!showForm" @click="showForm = true" class="login-btn">登录</button>
      <div v-else class="auth-forms">
        <div class="form-container">
          <div class="form-header">
            <h2>{{ showLogin ? '登录' : '注册' }}</h2>
            <button @click="showForm = false" class="close-btn">&times;</button>
          </div>
          <form @submit.prevent="handleSubmit">
            <div class="form-group">
              <input
                v-model="username"
                type="text"
                placeholder="用户名"
                required
              />
            </div>
            <div class="form-group">
              <input
                v-model="password"
                type="password"
                placeholder="密码"
                required
              />
            </div>
            <button type="submit" class="submit-btn">
              {{ showLogin ? '登录' : '注册' }}
            </button>
          </form>
          <p class="toggle-text">
            {{ showLogin ? '没有账号？' : '已有账号？' }}
            <a href="#" @click.prevent="toggleForm">{{ 
              showLogin ? '立即注册' : '立即登录'
            }}</a>
          </p>
        </div>
      </div>
    </div>
    <div v-else class="user-info">
      <span>欢迎，{{ currentUser }}</span>
      <button @click="logout" class="logout-btn">退出登录</button>
    </div>
    <div v-if="message" class="message success">{{ message }}</div>
    <div v-if="error" class="message error">{{ error }}</div>
  </div>
</template>

<style scoped>
.user-auth {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 100;
}

.auth-forms {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #999;
}

.close-btn:hover {
  color: #333;
}

.form-group {
  margin-bottom: 15px;
}

input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.login-btn {
  padding: 8px 16px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.login-btn:hover {
  background-color: #3aa876;
}

.submit-btn {
  width: 100%;
  padding: 10px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.submit-btn:hover {
  background-color: #3aa876;
}

.toggle-text {
  text-align: center;
  margin-top: 10px;
  font-size: 14px;
}

.toggle-text a {
  color: #42b983;
  text-decoration: none;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logout-btn {
  padding: 5px 10px;
  background-color: #ff6b6b;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.message {
  margin-top: 10px;
  padding: 8px;
  border-radius: 4px;
  text-align: center;
}

.success {
  background-color: #d4edda;
  color: #155724;
}

.error {
  background-color: #f8d7da;
  color: #721c24;
}
</style>