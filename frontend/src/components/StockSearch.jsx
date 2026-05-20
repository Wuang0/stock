import React, { useState } from 'react'

// 合法股票代码：字母、数字、点、连字符、^（指数）
const SYMBOL_RE = /^[A-Z0-9.\-^]+$/

export default function StockSearch({ onSearch, loading }) {
  const [symbol, setSymbol] = useState('')
  const [invalid, setInvalid] = useState(false)

  const handleChange = (e) => {
    const val = e.target.value
    setSymbol(val)
    setInvalid(false)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const trimmed = symbol.trim().toUpperCase()
    if (!trimmed) return
    if (!SYMBOL_RE.test(trimmed)) {
      setInvalid(true)
      return
    }
    onSearch(trimmed)
  }

  return (
    <div className="search-card">
      <form className="search-form" onSubmit={handleSubmit}>
        <div className="search-input-wrap">
          <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
          </svg>
          <input
            type="text"
            value={symbol}
            onChange={handleChange}
            placeholder="输入股票代码，如 AAPL, 0700.HK, 600519"
            disabled={loading}
            className={`search-input${invalid ? ' is-invalid' : ''}`}
          />
        </div>
        <button type="submit" disabled={loading || !symbol.trim()} className="btn-search">
          {loading ? '查询中...' : '查询行情'}
        </button>
      </form>
      {invalid && <p className="search-hint">代码格式不正确，仅支持字母、数字、. - ^</p>}
    </div>
  )
}
