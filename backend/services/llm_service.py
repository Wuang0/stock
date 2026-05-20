import json
import time
import logging
from openai import OpenAI, APIConnectionError, RateLimitError, APITimeoutError, APIStatusError
from config import LLM_API_KEY, LLM_API_BASE, LLM_MODEL

logger = logging.getLogger(__name__)

# 重试配置
MAX_RETRIES = 2
RETRY_DELAY = 1  # 基础等待秒数
RETRY_BACKOFF = 2  # 指数退避倍数


class LLMServiceError(Exception):
    """LLM服务调用异常"""
    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


def _create_client() -> OpenAI:
    """创建带超时配置的OpenAI客户端"""
    return OpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_API_BASE,
        timeout=30.0,
        max_retries=0,  # 由我们自己控制重试逻辑
    )


def analyze_stock(stock_data: dict) -> dict:
    """调用LLM分析股票数据，返回严格JSON格式。包含重试和异常处理。"""
    client = _create_client()

    # 构建精简的股票数据摘要给LLM
    price_history_str = "\n".join(
        f"  {p['date']}: 收盘{p['close']} 成交量{p['volume']}"
        for p in stock_data["price_history"]
    )

    prompt = f"""你是一位专业的股票分析师。请根据以下股票数据进行分析。

股票: {stock_data['name']} ({stock_data['symbol']})
当前价格: {stock_data['current_price']} {stock_data['currency']}
前收盘价: {stock_data['previous_close']}
涨跌幅: {stock_data['change_pct']}%
市盈率: {stock_data['pe_ratio']}
市值: {stock_data['market_cap']}
52周最高: {stock_data['52week_high']}
52周最低: {stock_data['52week_low']}
日成交量: {stock_data['volume']}

近30天价格走势:
{price_history_str}

【极其重要】你必须严格遵守以下规则：
1. 只返回纯 JSON 文本，不要 markdown 代码块（不要 ```json）
2. 不要任何解释、前言、后缀文字
3. 不要添加 JSON 中未定义的字段
4. 确保 JSON 语法正确：字符串用双引号，末尾无多余逗号
5. sentiment 只能是 "Bullish"、"Neutral" 或 "Bearish" 之一
6. risk_level 只能是 "Low"、"Medium" 或 "High" 之一
7. key_factors 必须是字符串数组，恰好 3 个元素

请严格按照以下JSON格式返回分析结果，不要包含任何其他文字:
{{
  "summary": "对股票当前状况的总结分析(100-200字)",
  "sentiment": "Bullish或Neutral或Bearish",
  "risk_level": "Low或Medium或High",
  "key_factors": ["关键因素1", "关键因素2", "关键因素3"],
  "recommendation": "买入/持有/卖出的建议说明"
}}"""

    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "你是一位专业的股票分析师，始终以严格的JSON格式返回分析结果。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            # 检查响应内容是否为空
            content = response.choices[0].message.content
            if not content:
                raise LLMServiceError("LLM返回内容为空", retryable=True)

            result = json.loads(content)

            # 确保必需字段存在
            return {
                "summary": result.get("summary", "分析暂不可用"),
                "sentiment": result.get("sentiment", "Neutral"),
                "risk_level": result.get("risk_level", "Medium"),
                "key_factors": result.get("key_factors", []),
                "recommendation": result.get("recommendation", ""),
            }

        except (RateLimitError, APITimeoutError) as e:
            last_error = e
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                logger.warning(f"LLM请求限流/超时(第{attempt + 1}次)，{delay}秒后重试: {e}")
                time.sleep(delay)
                continue

        except APIConnectionError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                logger.warning(f"LLM连接失败(第{attempt + 1}次)，{delay}秒后重试: {e}")
                time.sleep(delay)
                continue

        except APIStatusError as e:
            # 服务端错误(5xx)可重试，客户端错误(4xx)不重试
            if e.status_code >= 500:
                last_error = e
                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                    logger.warning(f"LLM服务端错误(第{attempt + 1}次)，{delay}秒后重试: {e}")
                    time.sleep(delay)
                    continue
            # 4xx 客户端错误（如认证失败、参数错误），不重试
            logger.error(f"LLM API客户端错误({e.status_code}): {e}")
            raise LLMServiceError(f"LLM API请求失败({e.status_code}): {e.message}", retryable=False)

        except json.JSONDecodeError as e:
            # JSON解析失败，重试无意义
            logger.error(f"LLM返回的JSON解析失败: {e}")
            raise LLMServiceError("LLM返回内容格式异常，JSON解析失败", retryable=False)

        except (KeyError, IndexError) as e:
            # 响应结构异常，可重试
            last_error = e
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                logger.warning(f"LLM响应结构异常(第{attempt + 1}次)，{delay}秒后重试: {e}")
                time.sleep(delay)
                continue

        break  # 非重试场景，跳出循环

    # 所有重试耗尽
    logger.error(f"LLM分析失败，已达最大重试次数: {last_error}")
    raise LLMServiceError(f"AI分析服务暂时不可用，请稍后重试", retryable=True)
