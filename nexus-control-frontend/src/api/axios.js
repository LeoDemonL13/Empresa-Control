import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: { 'X-Requested-With': 'XMLHttpRequest' },
})

export default api
