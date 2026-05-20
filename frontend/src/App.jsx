import React, { useState, useEffect, useRef, useCallback } from 'react'
import StockSearch from './components/StockSearch'
import StockData from './components/StockData'
import AIAnalysis from './components/AIAnalysis'
import { fetchStockData, analyzeStock, fetchRecords } from './services/api'
import './App.css'

const REFRESH_INTERVAL = 10 * 1000

export default function App() {
  const [stockData, setStockData] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState('')
  const [symbol, setSymbol] = useState('')
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [countdown, setCountdown] = useState(10)
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem('stock-theme') || 'dark' } catch { return 'dark' }
  })
  const timerRef = useRef(null)
  const countdownRef = useRef(null)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try { localStorage.setItem('stock-theme', theme) } catch {}
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark')
  }

  const refreshData = useCallback(async (sym) => {
    const target = sym || symbol
    if (!target) return
    try {
      const res = await fetchStockData(target)
      setStockData(res.data)
    } catch {
      // 静默失败
    }
  }, [symbol])

  const handleSearch = async (sym) => {
    setLoading(true)
    setError('')
    setAnalysis(null)
    setAutoRefresh(false)
    setSymbol(sym)
    try {
      const res = await fetchStockData(sym)
      setStockData(res.data)
    } catch (err) {
      setError(err.message)
      setStockData(null)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async () => {
    if (!symbol) return
    setAnalyzing(true)
    setError('')
    try {
      const res = await analyzeStock(symbol, stockData)
      setAnalysis(res.data?.analysis)
    } catch (err) {
      setError(err.message)
    } finally {
      setAnalyzing(false)
    }
  }

  const handleLoadRecords = async () => {
    try {
      const res = await fetchRecords()
      setRecords(res.data || [])
    } catch (err) {
      setError('历史记录不可用，请检查Supabase是否已配置')
    }
  }

  const toggleAutoRefresh = () => {
    setAutoRefresh(prev => !prev)
  }

  useEffect(() => {
    if (autoRefresh && symbol && stockData) {
      setCountdown(10)
      timerRef.current = setInterval(() => {
        refreshData(symbol)
        setCountdown(10)
      }, REFRESH_INTERVAL)

      countdownRef.current = setInterval(() => {
        setCountdown(prev => (prev <= 1 ? 10 : prev - 1))
      }, 1000)
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      if (countdownRef.current) clearInterval(countdownRef.current)
    }
  }, [autoRefresh, symbol, stockData, refreshData])

  useEffect(() => {
    setAutoRefresh(false)
  }, [symbol])

  const showAnalysis = analysis || analyzing

  return (
    <div className="app">
      <div className="top-accent" />

      <button className="theme-toggle" onClick={toggleTheme} title={theme === 'dark' ? '切换亮色主题' : '切换暗色主题'}>
        <svg className="theme-toggle-icon-light" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
        <svg className="theme-toggle-icon-dark" viewBox="0 0 24 24">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      </button>

      <header className="app-header">
        <div className="header-brand">
          <span className="header-tag">STOCK</span>
          <h1>AI Analyzer</h1>
        </div>
        <p className="header-sub">实时行情 · 智能分析 · 数据驱动</p>
      </header>

      <main className="app-main">
        <StockSearch onSearch={handleSearch} loading={loading} />

        {error && <div className="error-msg">{error}</div>}

        {loading && (
          <div className="skeleton-card fade-in">
            <div className="skeleton-row">
              <div className="skeleton-block" style={{ width: 140, height: 28 }} />
              <div className="skeleton-block" style={{ width: 90, height: 34 }} />
            </div>
            <div className="skeleton-grid">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="skeleton-cell" />
              ))}
            </div>
            <div className="skeleton-chart-area" />
          </div>
        )}

        {stockData && !loading && (
          <div className={`content-grid ${showAnalysis ? 'has-analysis' : ''}`} key={symbol}>
            <div className="content-main fade-in">
              <div className="refresh-bar">
                <button
                  className={`refresh-toggle ${autoRefresh ? 'active' : ''}`}
                  onClick={toggleAutoRefresh}
                >
                  <span className="refresh-dot" />
                  <span>{autoRefresh ? '自动刷新中' : '自动刷新'}</span>
                  {autoRefresh && <span className="refresh-countdown">{countdown}s</span>}
                </button>
                <span className="refresh-hint">每10秒更新</span>
              </div>
              <StockData
                data={stockData}
                onAnalyze={handleAnalyze}
                analyzing={analyzing}
              />
            </div>

            {showAnalysis && (
              <div className="content-side fade-in-delay">
                {analyzing && !analysis ? (
                  <div className="analysis-card is-analyzing">
                    <div className="scanline" />
                    <div className="analyzing-header">
                      <span className="analyzing-title">AI 分析中</span>
                      <span className="analyzing-dots">
                        <span /><span /><span />
                      </span>
                    </div>
                    <div className="placeholder-lines">
                      <div className="placeholder-line" />
                      <div className="placeholder-line short" />
                      <div className="placeholder-line" />
                      <div className="placeholder-line short" />
                    </div>
                    <p className="placeholder-text">正在分析市场数据和趋势...</p>
                  </div>
                ) : analysis ? (
                  <AIAnalysis analysis={analysis} />
                ) : null}
              </div>
            )}
          </div>
        )}

        <div className="records-section">
          <button className="btn-records" onClick={handleLoadRecords}>
            <span className="btn-records-icon">↻</span>
            查看历史记录
          </button>
          {records.length === 0 && (
            <p className="no-records">暂无历史分析记录</p>
          )}
          {records.length > 0 && (
            <div className="records-list fade-in">
              <div className="records-header">
                <h3>历史分析记录</h3>
                <span className="records-count">{records.length}</span>
              </div>
              {records.map((r) => (
                <div key={r.id} className="record-card">
                  <div className="record-main">
                    <strong className="record-name">{r.stock_name || r.symbol}</strong>
                    <span className="record-symbol">{r.symbol}</span>
                    <span className="record-time">
                      {new Date(r.created_at).toLocaleString('zh-CN')}
                    </span>
                  </div>
                  <p className="record-summary">{r.summary}</p>
                  <div className="record-tags">
                    <span className={`tag sentiment-${r.sentiment?.toLowerCase()}`}>
                      {r.sentiment}
                    </span>
                    <span className={`tag risk-${r.risk_level?.toLowerCase()}`}>
                      {r.risk_level}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
