const API_BASE = import.meta.env.VITE_API_BASE_URL
  || (import.meta.env.DEV ? '/api' : 'https://stock-ai-backend-2622.onrender.com/api')

export async function fetchStockData(symbol) {
  const res = await fetch(`${API_BASE}/stock/${encodeURIComponent(symbol)}`)
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || '获取股票数据失败')
  }
  return res.json()
}

export async function analyzeStock(symbol, stockData = null) {
  // 提交任务
  const submitRes = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol, stock_data: stockData }),
  })
  if (!submitRes.ok) {
    const err = await submitRes.json()
    throw new Error(err.detail || '分析失败')
  }
  const submitData = await submitRes.json()

  // 兼容：如果后端直接返回了 data（同步模式）
  if (submitData.data) {
    return submitData
  }

  // 异步模式：轮询结果
  const taskId = submitData.task_id
  const POLL_INTERVAL = 2000
  const MAX_POLLS = 60
  for (let i = 0; i < MAX_POLLS; i++) {
    await new Promise(r => setTimeout(r, POLL_INTERVAL))
    const pollRes = await fetch(`${API_BASE}/task/${taskId}`)
    if (!pollRes.ok) continue
    const result = await pollRes.json()
    if (result.status === 'done' && result.data) {
      return { success: true, data: result.data }
    }
    if (result.status === 'error') {
      throw new Error(result.error || '分析失败')
    }
  }
  throw new Error('分析超时，请稍后重试')
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
