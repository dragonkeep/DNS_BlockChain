// 区块链DNS API服务

const API_BASE_URL = 'http://127.0.0.1:5173';
// API函数
export const mockApi = {
  // 查询域名 - 使用XMLHttpRequest避免循环调用
  async resolveDomain(hostname: any) {
    try {
      // 使用XMLHttpRequest避免被apiInterceptor拦截
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE_URL}/dns/request`);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function() {
          if (xhr.status >= 200 && xhr.status < 300) {
            const data = JSON.parse(xhr.responseText);
            resolve({ success: true, hostname, ip: data.ip, port: data.port });
          } else {
            reject(new Error('域名未找到'));
          }
        };
        xhr.onerror = function() {
          reject(new Error('域名未找到'));
        };
        xhr.send(JSON.stringify({ hostname }));
      });
    } catch (error) {
      console.error('查询域名错误:', error);
      throw new Error('域名未找到');
    }
  },

  // 创建钱包
  async createWallet() {
    try {
      const response = await fetch(`${API_BASE_URL}/wallet/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('创建钱包失败');
      }
      
      return await response.json();
    } catch (error) {
      console.error('创建钱包错误:', error);
      throw error;
    }
  },
  
  // 导入钱包
  async importWallet(data: any) {
    try {
      const response = await fetch(`${API_BASE_URL}/wallet/import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '导入钱包失败');
      }
      
      return await response.json();
    } catch (error) {
      console.error('导入钱包错误:', error);
      throw error;
    }
  },
  
  // 获取钱包信息
  async getWalletInfo(address: string) {
    try {
      const response = await fetch(`${API_BASE_URL}/wallet/info/${address}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '获取钱包信息失败');
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取钱包信息错误:', error);
      throw error;
    }
  },
  
  // 注册域名 - 使用XMLHttpRequest避免循环调用
  async registerDomain(data:any) {
    try {
      // 使用XMLHttpRequest避免被apiInterceptor拦截
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE_URL}/dns/register`);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function() {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            try {
              const errorData = JSON.parse(xhr.responseText);
              reject(new Error(errorData.error || '注册域名失败'));
            } catch (e) {
              reject(new Error('注册域名失败'));
            }
          }
        };
        xhr.onerror = function() {
          reject(new Error('注册域名失败'));
        };
        xhr.send(JSON.stringify({
          hostname: data.hostname,
          ip: data.ip,
          port: data.port,
          lease_years: data.lease_years
        }));
      });
    } catch (error) {
      console.error('注册域名错误:', error);
      throw error;
    }
  },
  
  // 添加DNS记录 - 使用XMLHttpRequest避免循环调用，并统一数据结构
  async addDnsRecord(data: any) {
    try {
      // 使用XMLHttpRequest避免被apiInterceptor拦截
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE_URL}/dns/new`);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function() {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            try {
              const errorData = JSON.parse(xhr.responseText);
              reject(new Error(errorData.error || '添加DNS记录失败'));
            } catch (e) {
              reject(new Error('添加DNS记录失败'));
            }
          }
        };
        xhr.onerror = function() {
          reject(new Error('添加DNS记录失败'));
        };
        
        // 统一使用指定的数据结构格式
        const payload = {
          entry: {
            hostname: data.entry.hostname,
            type: data.entry.type,
            value: data.entry.value,
            ip: data.entry.ip,      
            port: data.entry.port, 
            wallet_address: data.entry.wallet_address || ''
          }
        };
        
        xhr.send(JSON.stringify(payload));
      });
    } catch (error) {
      console.error('添加DNS记录错误:', error);
      throw error;
    }
  },
  
  // 获取区块链状态 - 使用原始fetch避免循环调用
  async getBlockchainStatus() {
    try {
      // 使用原始XMLHttpRequest避免被apiInterceptor拦截
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('GET', `${API_BASE_URL}/nodes/chain?type=dns`);
        xhr.onload = function() {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            reject(new Error('获取区块链状态失败'));
          }
        };
        xhr.onerror = function() {
          reject(new Error('获取区块链状态失败'));
        };
        xhr.send();
      });
    } catch (error) {
      console.error('获取区块链状态错误:', error);
      throw error;
    }
  },
  
  // 获取注册区块链状态 - 使用原始fetch避免循环调用
  async getRegisterBlockchainStatus() {
    try {
      // 使用原始XMLHttpRequest避免被apiInterceptor拦截
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('GET', `${API_BASE_URL}/nodes/chain?type=register`);
        xhr.onload = function() {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            reject(new Error('获取注册区块链状态失败'));
          }
        };
        xhr.onerror = function() {
          reject(new Error('获取注册区块链状态失败'));
        };
        xhr.send();
      });
    } catch (error) {
      console.error('获取注册区块链状态错误:', error);
      throw error;
    }
  },
  
  // 获取代币余额
  async getTokenBalance(nodeId: string) {
    try {
      const response = await fetch(`${API_BASE_URL}/tokens/balance?node_id=${nodeId}`);
      
      if (!response.ok) {
        throw new Error('获取代币余额失败');
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取代币余额错误:', error);
      throw error;
    }
  },
  
  // 转账代币
  async transferTokens(fromNode: string, toNode: string, amount: number) {
    try {
      const response = await fetch(`${API_BASE_URL}/tokens/transfer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          from_node: fromNode,
          to_node: toNode,
          amount: amount
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '转账失败');
      }
      
      return await response.json();
    } catch (error) {
      console.error('转账错误:', error);
      throw error;
    }
  }
};