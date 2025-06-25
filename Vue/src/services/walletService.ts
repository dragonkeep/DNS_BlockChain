// 钱包管理服务 - 调用后端API实现钱包功能
import { ref } from 'vue';
import axios from 'axios';

// API基础URL
const API_BASE_URL = 'http://127.0.0.1:5000';

// 存储钱包数据的响应式引用
export const wallets = ref([]);

// 钱包服务
export const walletService = {
  // 检查钱包状态
  async checkWalletStatus() {
    try {
      const response = await axios.get(`${API_BASE_URL}/wallet/status`);
      return response.data;
    } catch (error) {
      console.error('检查钱包状态失败:', error);
      return { connected: false, message: '无法连接到服务器' };
    }
  },
  
  // 创建新钱包
  async createWallet() {
    try {
      const response = await axios.post(`${API_BASE_URL}/wallet/create`);
      return response.data;
    } catch (error) {
      console.error('创建钱包失败:', error);
      throw new Error('创建钱包失败');
    }
  },
  
  // 导入现有钱包
  async importWallet(privateKey: string) {
    try {
      const response = await axios.post(`${API_BASE_URL}/wallet/import`, {
        private_key: privateKey
      });
      return response.data;
    } catch (error) {
      console.error('导入钱包失败:', error);
      throw new Error('导入钱包失败');
    }
  },
  
  // 获取钱包信息
  async getWalletInfo(address: string) {
    try {
      const response = await axios.get(`${API_BASE_URL}/wallet/info/${address}`);
      return response.data;
    } catch (error) {
      console.error('获取钱包信息失败:', error);
      throw new Error('获取钱包信息失败');
    }
  },
  
  // 清除钱包信息
  async clearWalletInfo() {
    try {
      // 通知后端断开钱包连接
      await axios.post(`${API_BASE_URL}/wallet/disconnect`);
      // 清除前端存储的钱包数据
      wallets.value = [];
      localStorage.removeItem('walletAddress');
      return { success: true, message: '钱包信息已清除' };
    } catch (error) {
      console.error('清除钱包信息失败:', error);
      throw new Error('清除钱包信息失败');
    }
  }
};