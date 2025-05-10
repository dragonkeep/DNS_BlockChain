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
      
      // DNS解析API
      if (url.match(/\/dns\/resolve\/.+/)) {
        const hostname = url.split('/').pop() || '';
        responseData = await mockApi.resolveDomain(hostname);
      }
      // 域名注册API
      else if (url === '/dns/register' && method === 'POST') {
        responseData = await mockApi.registerDomain(body);
      }
      // 添加DNS记录API
      else if (url === '/dns/new' && method === 'POST') {
        responseData = await mockApi.addDnsRecord(body);
      }
      // 获取DNS区块链状态
      else if (url === '/chain') {
        responseData = await mockApi.getBlockchainStatus();
      }
      // 获取注册区块链状态
      else if (url === '/register_chain') {
        responseData = await mockApi.getRegisterBlockchainStatus();
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
    } catch (error) {
      // 返回错误响应
      return new Response(JSON.stringify({ error: error.message }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  };
}