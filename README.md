# Stock AI Analyzer

基于 LLM 的智能股票分析工具，支持 A 股、美股、港股行情查询与 AI 分析。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Vite 6，纯 CSS 变量主题系统，SVG 原生图表 |
| 后端 | FastAPI + Uvicorn |
| 行情数据 | baostock（A 股）+ yfinance（美股/港股） |
| AI 分析 | 智谱清言（OpenAI 兼容接口） |
| 数据存储 | Supabase（PostgreSQL） |

## 功能特性

- **多市场支持** — A 股（6 位代码如 `600519`）、美股（`AAPL`）、港股（`0700.HK`）、指数（`^GSPC`）
- **AI 智能分析** — 调用 LLM 生成市场情绪、风险等级、关键因素、投资建议
- **实时行情** — 股价、涨跌幅、市盈率、市值、52 周高低、近 30 天走势图
- **自动刷新** — 10 秒间隔自动更新行情数据
- **深色/浅色主题** — 终端黑金风格，一键切换
- **历史记录** — 分析结果持久化存储，支持按股票代码查询

## 项目结构

```
stock/
├── supabase-schema.sql          # 数据库建表 SQL
├── backend/
│   ├── app.py                   # FastAPI 主应用
│   ├── config.py                # 配置加载
│   ├── .env.example             # 环境变量模板
│   ├── requirements.txt         # Python 依赖
│   └── services/
│       ├── stock_service.py     # 股票数据获取
│       ├── llm_service.py       # LLM 分析服务
│       └── db_service.py        # 数据库操作
└── frontend/
    ├── package.json
    ├── vite.config.js           # Vite 配置（含 API 代理）
    └── src/
        ├── App.jsx              # 主应用组件
        ├── App.css              # 主题样式
        ├── services/
        │   └── api.js           # 后端 API 封装
        └── components/
            ├── StockSearch.jsx  # 股票搜索
            ├── StockData.jsx    # 行情展示 + 走势图
            └── AIAnalysis.jsx   # AI 分析结果
```

## 快速开始

### 1. 环境准备

- Python 3.10+
- Node.js 18+

### 2. 配置后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 复制环境变量模板并填写
cp .env.example .env
```

编辑 `.env` 文件，填入以下配置：

```env
# 智谱清言 API（https://open.bigmodel.cn 注册获取）
LLM_API_KEY=your_zhipu_api_key_here
LLM_API_BASE=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4-flash

# Supabase（可选，不配置则跳过数据持久化）
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key_here
```

### 3. 配置数据库（可选）

如需使用分析记录持久化，在 Supabase 中执行 `supabase-schema.sql` 建表。

### 4. 启动后端

```bash
cd backend
python app.py
```

后端运行在 `http://localhost:8000`。

### 5. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行在 `http://localhost:3000`，API 请求自动代理到后端。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/stock/{symbol}` | 获取股票行情数据 |
| `POST` | `/api/analyze` | AI 分析股票（请求体：`{"symbol": "AAPL", "stock_data": {...}}`） |
| `GET` | `/api/records?symbol=&limit=20` | 查询历史分析记录 |

## LLM 异常处理

LLM 调用层内置了完善的异常处理机制：

- **自动重试** — 限流(429)、超时、网络断连、服务端错误(5xx) 最多重试 2 次，指数退避
- **快速失败** — 认证失败(4xx)、JSON 解析错误等不可恢复异常直接抛出
- **超时控制** — 请求超时 30 秒，避免无限挂起
- **错误分类** — 可重试错误返回 503，不可重试错误返回 500，便于前端区分处理

## Prompt 工程：强制 LLM 只输出 JSON

LLM 默认倾向于"说话"，会加上 `好的，以下是分析结果：` 或 ```` ```json ```` 代码块等冗余文本，导致后端 `json.loads()` 直接报错。本项目通过**三层约束**彻底解决这个问题。

### 三层约束机制

| 层级 | 手段 | 作用 |
|------|------|------|
| Prompt 规则 | 7 条显式约束指令 | 从语义层禁止多余输出 |
| API 参数 | `response_format={"type": "json_object"}` | 从模型层强制 JSON 模式 |
| 代码兜底 | `.get()` 默认值 + `JSONDecodeError` 捕获 | 解析层容错 |

### Prompt 规则（`llm_service.py:57-73`）

```python
【极其重要】你必须严格遵守以下规则：
1. 只返回纯 JSON 文本，不要 markdown 代码块（不要 ```json）
2. 不要任何解释、前言、后缀文字
3. 不要添加 JSON 中未定义的字段
4. 确保 JSON 语法正确：字符串用双引号，末尾无多余逗号
5. sentiment 只能是 "Bullish"、"Neutral" 或 "Bearish" 之一
6. risk_level 只能是 "Low"、"Medium" 或 "High" 之一
7. key_factors 必须是字符串数组，恰好 3 个元素

请严格按照以下JSON格式返回分析结果，不要包含任何其他文字:
{
  "summary": "对股票当前状况的总结分析(100-200字)",
  "sentiment": "Bullish或Neutral或Bearish",
  "risk_level": "Low或Medium或High",
  "key_factors": ["关键因素1", "关键因素2", "关键因素3"],
  "recommendation": "买入/持有/卖出的建议说明"
}
```

**设计要点：**

- **【极其重要】** 开头标记 — 提升规则的注意力权重，LLM 对强调标记更敏感
- **正向 + 反向约束** — 不仅说"返回 JSON"，还明确说"不要 ```json""不要前言"——只说"返回 JSON"时 LLM 仍然会用代码块包裹
- **枚举值锁定** — 规则 5/6 锁定字段取值范围，避免 LLM 自创 `"看涨"` 等非标准值
- **结构约束** — 规则 7 限定数组长度，避免返回 1 个或 10 个因素
- **示例模板** — 末尾给出完整 JSON 骨架，LLM 做 fill-in-the-blank 比从零生成更可靠

### API 参数层

```python
response = client.chat.completions.create(
    ...
    response_format={"type": "json_object"},  # 模型层面强制 JSON 模式
)
```

`response_format={"type": "json_object"}` 让模型在推理时只走 JSON token 路径，配合 system message 中的"始终以严格的JSON格式返回"形成双重锁定。

### 代码兜底层

```python
content = response.choices[0].message.content
if not content:
    raise LLMServiceError("LLM返回内容为空", retryable=True)

result = json.loads(content)  # 如果仍不是合法 JSON，抛出 JSONDecodeError

return {
    "summary": result.get("summary", "分析暂不可用"),   # 字段缺失时给默认值
    "sentiment": result.get("sentiment", "Neutral"),
    ...
}
```

即使前两层约束生效，仍可能因网络截断、模型幻觉等产生残缺 JSON，因此代码层用 `.get()` 兜底 + `JSONDecodeError` 捕获，确保不会因格式问题导致 500 错误。

## Debug 记录：LLM 返回非法 JSON 导致分析接口 500

### 问题现象

前端点击"AI 智能分析"后，请求 `/api/analyze` 返回 500，后端日志：

```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

### 排查过程

**第一步：定位报错位置**

`json.loads()` 在 `llm_service.py:59` 抛出异常，说明 `response.choices[0].message.content` 不是合法 JSON。

**第二步：打印原始响应内容**

临时加日志查看 LLM 实际返回了什么：

```python
raw = response.choices[0].message.content
print(f"[DEBUG] LLM raw response:\n{raw}")
```

发现 LLM 返回了以下内容：

```
好的，以下是对该股票的分析：

```json
{
  "summary": "贵州茅台近期表现...",
  "sentiment": "Bullish",
  ...
}
```

希望对您有所帮助！

**第三步：分析根因**

LLM "说话了"——在 JSON 前加了前言和代码块标记，在 JSON 后加了后缀。这是 LLM 的默认行为倾向，单纯在 prompt 中说"返回 JSON"不够，模型仍然会加修饰文字。

**第四步：修复**

三层修复，逐步收紧约束：

| 修复                       | 代码变更                                             |
| -------------------------- | ---------------------------------------------------- |
| Prompt 加 7 条显式规则     | 明确禁止代码块、前言、后缀，锁定字段枚举值           |
| API 参数 `response_format` | `{"type": "json_object"}` 强制模型走 JSON token 路径 |
| 代码层兜底                 | `json.loads()` 异常捕获 + `.get()` 默认值            |

修复后 LLM 返回纯 JSON，问题解决。

### 教训

> "对 LLM 说请返回 JSON" 和 "让 LLM 只能返回 JSON" 是两回事。Prompt 约束是"请"，`response_format` 是"必须"，代码兜底是"保险"——三层缺一不可。

