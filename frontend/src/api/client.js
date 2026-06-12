import axios from 'axios'

// Risk scoring API. Change the port here if you ran uvicorn on a different one.
export const riskClient = axios.create({
  baseURL: 'http://localhost:8500',
  headers: { 'Content-Type': 'application/json' }
})

export const scoreTransaction = async (txn) => {
  const { data } = await riskClient.post('/score', txn)
  return data
}

export const getAccount = async (accountId) => {
  const { data } = await riskClient.get(`/account/${accountId}`)
  return data
}

export const health = async () => {
  const { data } = await riskClient.get('/health')
  return data
}
