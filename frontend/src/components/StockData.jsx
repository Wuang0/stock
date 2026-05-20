import React from 'react'

export default function StockData({ data, onAnalyze, analyzing }) {
  if (!data) return null

  const isUp = data.change_pct >= 0

  return (
    <div className="stock-card">
      <div className="stock-header">
        <div className="stock-identity">
          <h2>{data.name}</h2>
          <span className="stock-symbol-badge">{data.symbol}</span>
        </div>
        <div className="stock-price-block">
          <span className="stock-current-price">{data.current_price}</span>
          <span className="stock-currency">{data.currency}</span>
          <span className={`stock-change-badge ${isUp ? 'up' : 'down'}`}>
            {isUp ? '+' : ''}{data.change_pct}%
          </span>
        </div>
      </div>

      <div className="stock-metrics-grid">
        <div className="metric-item">
          <span className="metric-label">前收盘</span>
          <span className="metric-value">{data.previous_close}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">日最高</span>
          <span className="metric-value">{data.day_high}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">日最低</span>
          <span className="metric-value">{data.day_low}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">成交量</span>
          <span className="metric-value">{(data.volume / 1e6).toFixed(2)}M</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">市盈率</span>
          <span className="metric-value">{data.pe_ratio ?? 'N/A'}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">市值</span>
          <span className="metric-value">{data.market_cap ? `${(data.market_cap / 1e9).toFixed(2)}B` : 'N/A'}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">52周高</span>
          <span className="metric-value">{data['52week_high']}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">52周低</span>
          <span className="metric-value">{data['52week_low']}</span>
        </div>
      </div>

      {data.price_history && data.price_history.length > 0 && (
        <div className="chart-section">
          <div className="chart-title">近30天走势</div>
          <div className="chart-wrapper">
            <MiniChart data={data.price_history} />
          </div>
        </div>
      )}

      <button
        className="btn-analyze"
        onClick={onAnalyze}
        disabled={analyzing}
      >
        {analyzing ? 'AI 分析中...' : (
          <>
            <span>AI 智能分析</span>
            <span className="btn-analyze-arrow">→</span>
          </>
        )}
      </button>
    </div>
  )
}

function MiniChart({ data }) {
  if (!data || data.length === 0) return null

  const closes = data.map(d => d.close)
  const min = Math.min(...closes)
  const max = Math.max(...closes)
  const range = max - min || 1

  const W = 640, H = 200
  const PX = 8, PY = 16
  const cW = W - PX * 2, cH = H - PY * 2

  const toX = i => PX + (i / Math.max(closes.length - 1, 1)) * cW
  const toY = v => PY + cH - ((v - min) / range) * cH

  const pts = closes.map((v, i) => `${toX(i)},${toY(v)}`).join(' ')
  const area = `${PX},${PY + cH} ${pts} ${PX + cW},${PY + cH}`
  const isUp = closes[closes.length - 1] >= closes[0]
  const color = isUp ? '#00d26a' : '#ff2d55'

  const lastX = toX(closes.length - 1)
  const lastY = toY(closes[closes.length - 1])

  const gridLines = Array.from({ length: 5 }, (_, i) => PY + (i / 4) * cH)

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg">
      <defs>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.18" />
          <stop offset="100%" stopColor={color} stopOpacity="0.01" />
        </linearGradient>
        <filter id="lineGlow">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {gridLines.map((gy, i) => (
        <line
          key={i}
          x1={PX} y1={gy} x2={PX + cW} y2={gy}
          stroke="var(--chart-grid)"
          strokeWidth="1"
        />
      ))}

      <polygon points={area} fill="url(#areaGrad)" />

      <polyline
        points={pts}
        fill="none"
        stroke={color}
        strokeWidth="5"
        opacity="0.2"
        filter="url(#lineGlow)"
      />

      <polyline
        points={pts}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="chart-line"
      />

      <circle
        cx={lastX} cy={lastY} r="8"
        fill={color} opacity="0"
        className="chart-pulse-ring"
      />

      <circle cx={lastX} cy={lastY} r="3" fill={color} />
    </svg>
  )
}
