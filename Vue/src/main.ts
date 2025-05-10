import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

// 导入API拦截器
import { setupApiInterceptor } from './services/apiInterceptor'

// 设置API拦截器（用于模拟API请求）
setupApiInterceptor()

const app = createApp(App)

app.use(createPinia())
app.use(router)

// 全局错误处理
app.config.errorHandler = (err, instance, info) => {
  console.error('全局错误:', err)
  console.info('错误信息:', info)
}

app.mount('#app')
