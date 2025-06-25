import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:5000',
  withCredentials: true // 允许跨域请求携带cookie
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response) {
      // 处理错误响应
      const { status, data } = error.response
      if (status === 401) {
        // 未登录或token过期
        console.error('未登录或登录已过期')
      }
    }
    return Promise.reject(error)
  }
)

export default api