-- Supabase 建表SQL
-- 在Supabase Dashboard的SQL Editor中执行

CREATE TABLE IF NOT EXISTS analysis_records (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100),
    current_price NUMERIC(18, 2),
    change_pct NUMERIC(10, 2),
    stock_data JSONB,
    summary TEXT,
    sentiment VARCHAR(20),
    risk_level VARCHAR(20),
    key_factors JSONB DEFAULT '[]',
    recommendation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引加速查询
CREATE INDEX IF NOT EXISTS idx_analysis_records_symbol ON analysis_records(symbol);
CREATE INDEX IF NOT EXISTS idx_analysis_records_created_at ON analysis_records(created_at DESC);

-- 设置RLS策略（按需开启）
ALTER TABLE analysis_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY "允许匿名读取" ON analysis_records FOR SELECT USING (true);
CREATE POLICY "允许匿名插入" ON analysis_records FOR INSERT WITH CHECK (true);
