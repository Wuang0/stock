const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export async function fetchStockData(symbol) {
  const res = await fetch(`${API_BASE}/stock/${encodeURIComponent(symbol)}`)
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || '获取股票数据失败')
  }
  return res.json()
}

export async function analyzeStock(symbol, stockData = null) {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol, stock_data: stockData }),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || '分析失败')
  }
  return res.json()
}

export async function fetchRecords(symbol = null) {
  const params = new URLSearchParams()
  if (symbol) params.set('symbol', symbol)
  const res = await fetch(`${API_BASE}/records?${params}`)
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || '获取记录失败')
  }
  return res.json()
}
