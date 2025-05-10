// 模拟区块链DNS API服务
import { ref } from 'vue';

// 模拟数据
const dnsRecords = ref([
  {
    hostname: 'example.com',
    ip: '192.168.1.100',
    port: 80,
    lease_expiry: Math.floor(Date.now() / 1000) + 31536000, // 当前时间 + 1年（秒）
    blockchain_type: 'DNS链'
  },
  {
    hostname: 'test.com',
    ip: '192.168.1.200',
    port: 443,
    lease_expiry: Math.floor(Date.now() / 1000) + 63072000, // 当前时间 + 2年（秒）
    blockchain_type: 'DNS链'
  },
  {
    hostname: 'blockchain.org',
    ip: '192.168.1.50',
    port: 8080,
    lease_expiry: Math.floor(Date.now() / 1000) + 94608000, // 当前时间 + 3年（秒）
    blockchain_type: '注册链'
  }
]);

// 模拟区块链状态
const dnsBlockchain = ref({
  length: 3,
  current_transactions: [
    { type: 'register', hostname: 'newdomain.com', timestamp: Date.now() / 1000 }
  ],
  chain: [
    {
      index: 1,
      timestamp: Math.floor(Date.now() / 1000) - 86400 * 3,
      transactions: [
        { type: 'register', hostname: 'example.com', ip: '192.168.1.100', port: 80 }
      ],
      hash: '0x1a2b3c4d5e6f'
    },
    {
      index: 2,
      timestamp: Math.floor(Date.now() / 1000) - 86400 * 2,
      transactions: [
        { type: 'register', hostname: 'test.com', ip: '192.168.1.200', port: 443 }
      ],
      hash: '0x2b3c4d5e6f7g'
    },
    {
      index: 3,
      timestamp: Math.floor(Date.now() / 1000) - 86400,
      transactions: [
        { type: 'register', hostname: 'blockchain.org', ip: '192.168.1.50', port: 8080 }
      ],
      hash: '0x3c4d5e6f7g8h'
    }
  ]
});

const registerBlockchain = ref({
  length: 2,
  current_transactions: [],
  chain: [
    {
      index: 1,
      timestamp: Math.floor(Date.now() / 1000) - 86400 * 2,
      transactions: [
        { type: 'token_issue', amount: 100, recipient: 'User1' }
      ],
      hash: '0x7g8h9i0j1k2l'
    },
    {
      index: 2,
      timestamp: Math.floor(Date.now() / 1000) - 86400,
      transactions: [
        { type: 'token_transfer', amount: 10, sender: 'User1', recipient: 'User2' }
      ],
      hash: '0x8h9i0j1k2l3m'
    }
  ]
});

// 模拟API函数
export const mockApi = {
  // 查询域名
  async resolveDomain(hostname: string) {
    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const record = dnsRecords.value.find(r => r.hostname === hostname);
    
    if (record) {
      return { success: true, ...record };
    } else {
      throw new Error('域名未找到');
    }
  },
  
  // 注册域名
  async registerDomain(data: { hostname: string, ip: string, port: number, lease_years: number }) {
    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // 检查域名是否已存在
    if (dnsRecords.value.some(r => r.hostname === data.hostname)) {
      throw new Error('域名已被注册');
    }
    
    // 创建新记录
    const newRecord = {
      hostname: data.hostname,
      ip: data.ip,
      port: data.port,
      lease_expiry: Math.floor(Date.now() / 1000) + (data.lease_years * 31536000),
      blockchain_type: 'DNS链'
    };
    
    // 添加到记录中
    dnsRecords.value.push(newRecord);
    
    // 添加交易到区块链
    dnsBlockchain.value.current_transactions.push({
      type: 'register',
      hostname: data.hostname,
      timestamp: Math.floor(Date.now() / 1000)
    });
    
    return { success: true, message: `域名 ${data.hostname} 注册成功！` };
  },
  
  // 添加DNS记录
  async addDnsRecord(data: { entry: { hostname: string, ip: string, port: number } }) {
    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 600));
    
    // 检查域名是否已存在
    if (dnsRecords.value.some(r => r.hostname === data.entry.hostname)) {
      throw new Error('域名已存在');
    }
    
    // 创建新记录
    const newRecord = {
      hostname: data.entry.hostname,
      ip: data.entry.ip,
      port: data.entry.port,
      lease_expiry: Math.floor(Date.now() / 1000) + 31536000, // 默认1年
      blockchain_type: 'DNS链'
    };
    
    // 添加到记录中
    dnsRecords.value.push(newRecord);
    
    // 添加交易到区块链
    dnsBlockchain.value.current_transactions.push({
      type: 'add_record',
      hostname: data.entry.hostname,
      timestamp: Math.floor(Date.now() / 1000)
    });
    
    return { success: true, message: `DNS记录 ${data.entry.hostname} 添加成功！` };
  },
  
  // 获取区块链状态
  async getBlockchainStatus() {
    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 700));
    
    return dnsBlockchain.value;
  },
  
  // 获取注册区块链状态
  async getRegisterBlockchainStatus() {
    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 700));
    
    return registerBlockchain.value;
  }
};