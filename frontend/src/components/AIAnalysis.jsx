import React from 'react'

const SENTIMENT_MAP = {
  Bullish: { label: '看涨', color: '#00d26a', icon: '↗', key: 'bullish' },
  Neutral: { label: '中性', color: '#ff9f0a', icon: '→', key: 'neutral' },
  Bearish: { label: '看跌', color: '#ff2d55', icon: '↘', key: 'bearish' },
}

const RISK_MAP = {
  Low: { label: '低风险', color: '#00d26a', icon: '◆', key: 'low' },
  Medium: { label: '中等风险', color: '#ff9f0a', icon: '◆', key: 'medium' },
  High: { label: '高风险', color: '#ff2d55', icon: '◆', key: 'high' },
}

export default function AIAnalysis({ analysis }) {
  if (!analysis) return null

  const sentiment = SENTIMENT_MAP[analysis.sentiment] || SENTIMENT_MAP.Neutral
  const risk = RISK_MAP[analysis.risk_level] || RISK_MAP.Medium

  return (
    <div className="analysis-card">
      <div className="analysis-header">
        <h3 className="analysis-title">AI 分析结果</h3>
        <span className="analysis-badge">AI</span>
      </div>

      <div className="analysis-indicators">
        <div className={`indicator indicator-sentiment-${sentiment.key}`}>
          <div className="indicator-visual">{sentiment.icon}</div>
          <div className="indicator-info">
            <span className="indicator-label">市场情绪</span>
            <span className="indicator-value">{sentiment.label}</span>
          </div>
        </div>
        <div className={`indicator indicator-risk-${risk.key}`}>
          <div className="indicator-visual">{risk.icon}</div>
          <div className="indicator-info">
            <span className="indicator-label">风险等级</span>
            <span className="indicator-value">{risk.label}</span>
          </div>
        </div>
      </div>

      <div className="analysis-section">
        <h4 className="section-title">分析总结</h4>
        <p className="summary-text">{analysis.summary}</p>
      </div>

      {analysis.key_factors && analysis.key_factors.length > 0 && (
        <div className="analysis-section">
          <h4 className="section-title">关键因素</h4>
          <ul className="factors-list">
            {analysis.key_factors.map((f, i) => (
              <li key={i} className="factor-item">
                <span className="factor-index">{String(i + 1).padStart(2, '0')}</span>
                <span className="factor-text">{f}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {analysis.recommendation && (
        <div className="analysis-section">
          <h4 className="section-title">投资建议</h4>
          <div className="recommendation-box">
            <p>{analysis.recommendation}</p>
          </div>
        </div>
      )}
    </div>
  )
}
