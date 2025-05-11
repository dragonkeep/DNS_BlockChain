<script setup lang="ts">
// 无需导入其他组件
</script>

<template>
  <div class="home-view">
    <div class="hero-section">
      <h1>欢迎使用区块链DNS系统</h1>
      <p class="subtitle">基于区块链技术的分布式域名系统</p>
    </div>
    
    <div class="features-section">
      
      <div class="feature-grid">
        <div class="feature-card">
          <div class="feature-icon">📝</div>
          <h3>域名管理</h3>
          <p>注册和管理您的域名，设置IP地址和端口信息</p>
          <router-link to="/register" class="feature-link">立即管理</router-link>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">🔍</div>
          <h3>域名查询</h3>
          <p>查询已注册域名的IP地址、端口和租约信息</p>
          <router-link to="/dns" class="feature-link">立即查询</router-link>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🪙</div>
          <h3>钱包管理</h3>
          <p>管理您的区块链钱包，进行转账和支付</p>
          <router-link to="/wallet" class="feature-link">管理钱包</router-link>
        </div>
        <div class="feature-card">
          <div class="feature-icon">⛓️</div>
          <h3>区块链状态</h3>
          <p>查看区块链的当前状态，包括区块数量和交易信息</p>
          <router-link to="/blockchain" class="feature-link">查看状态</router-link>
        </div>
      </div>
    </div>
    
    <div class="about-section">
      <h2>关于区块链DNS</h2>
      <p>区块链DNS系统是一个基于区块链技术的分布式域名系统，它提供了一种去中心化的方式来管理和解析域名。</p>
      <p>与传统DNS系统相比，区块链DNS具有以下优势：</p>
      <ul>
        <li>去中心化：没有单一控制点，更加安全可靠</li>
        <li>透明性：所有域名注册和解析记录都存储在区块链上，公开透明</li>
        <li>防篡改：区块链的不可变性确保域名记录不会被恶意篡改</li>
        <li>自主控制：用户完全控制自己的域名资产</li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.home-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.hero-section {
  text-align: center;
  margin-bottom: 40px;
}

.hero-section h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 10px;
}

.subtitle {
  font-size: 1.2rem;
  color: #666;
}

.features-section {
  margin-bottom: 40px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.feature-card {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
}

.feature-icon {
  font-size: 2rem;
  margin-bottom: 15px;
}

.feature-card h3 {
  margin-bottom: 10px;
  color: #2c3e50;
}

.feature-link {
  display: inline-block;
  margin-top: 10px;
  color: #42b983;
  text-decoration: none;
  font-weight: bold;
}

.feature-link:hover {
  text-decoration: underline;
}

.about-section {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.about-section h2 {
  color: #2c3e50;
  margin-bottom: 15px;
}

.about-section ul {
  margin-top: 10px;
  padding-left: 20px;
}

.about-section li {
  margin-bottom: 8px;
}
</style>
