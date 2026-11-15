import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 5000,
})

export async function getApiHealth() {
  const { data } = await api.get('/health')
  return data
}
