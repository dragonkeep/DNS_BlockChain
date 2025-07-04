// API拦截器 - 用于模拟API请求
import { mockApi } from './mockApi';

// 拦截fetch请求并使用模拟API响应
export function setupApiInterceptor() {
  // 保存原始fetch函数
  const originalFetch = window.fetch;
  
  // 重写fetch函数
  window.fetch = async function(input: RequestInfo | URL, init?: RequestInit) {
    const url = input.toString();
    
    // 解析请求信息
    let method = init?.method || 'GET';
    let body = init?.body ? JSON.parse(init.body.toString()) : null;
    
    try {
      // 根据URL路径和方法模拟不同的API响应
      let responseData;
      const urlPath = new URL(url, window.location.origin).pathname;
      // DNS解析API
      if (urlPath === '/dns/request' && method === 'POST') {
        responseData = await mockApi.resolveDomain(body.hostname);
      }
      // 域名注册API
      else if (urlPath === '/dns/register' && method === 'POST') {
        responseData = await mockApi.registerDomain(body);
      }
      // 添加DNS记录API
      else if (urlPath === '/dns/new' && method === 'POST') {
        responseData = await mockApi.addDnsRecord(body);
      }
      // 获取DNS区块链状态
      else if (urlPath === '/nodes/chain' && url.includes('type=dns')) {
        responseData = await mockApi.getBlockchainStatus();
      }
      // 获取注册区块链状态
      else if (urlPath === '/nodes/chain' && url.includes('type=register')) {
        responseData = await mockApi.getRegisterBlockchainStatus();
      }
      // 创建钱包
      else if (urlPath === '/wallet/create' && method === 'POST') {
        responseData = await mockApi.createWallet();
      }
      // 导入钱包
      else if (urlPath === '/wallet/import' && method === 'POST') {
        responseData = await mockApi.importWallet(body);
      }
      // 获取钱包信息
      else if (url.match(/\/wallet\/info\/.+/)) {
        const address = url.split('/').pop() || '';
        responseData = await mockApi.getWalletInfo(address);
      }
      // 未知API，返回404
      else {
        return new Response(JSON.stringify({ error: '未找到API' }), {
          status: 404,
          headers: { 'Content-Type': 'application/json' }
        });
      }
      
      // 返回成功响应
      return new Response(JSON.stringify(responseData), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (error: any) {
      return new Response(JSON.stringify({ error: error?.message || '未知错误' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  };
}