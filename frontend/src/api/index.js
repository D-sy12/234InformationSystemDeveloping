import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 20000 })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (resp) => resp.data,
  (error) => {
    const message = error.response?.data?.message || '网络请求失败，请稍后再试'
    const status = error.response?.status
    if (status === 401 && !location.pathname.startsWith('/login')) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      location.href = '/login'
    }
    return Promise.reject(new Error(message))
  },
)

export default api
