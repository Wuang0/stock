from typing import Optional
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.stock_service import get_stock_data
from services.llm_service import analyze_stock, LLMServiceError, _create_client
from services.db_service import save_analysis, get_analysis_records

app = FastAPI(title="Stock AI Analyzer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    symbol: str
    stock_data: Optional[dict] = None  # 前端传入已有的股票数据，避免重复请求


@app.get("/api/stock/{symbol}")
def fetch_stock(symbol: str):
    """获取股票行情数据"""
    try:
        data = get_stock_data(symbol.strip().upper())
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票数据失败: {str(e)}")


@app.post("/api/analyze")
def analyze_stock_data(req: AnalyzeRequest):
    """调用LLM分析股票并存储结果"""
    symbol = req.symbol.strip().upper()
    try:
        # 优先使用前端传入的股票数据，避免重复请求akshare
        if req.stock_data:
            stock_data = req.stock_data
        else:
            stock_data = get_stock_data(symbol)

        # 调用LLM分析
        analysis = analyze_stock(stock_data)

        # 存储到Supabase（如果配置了的话）
        record = None
        try:
            record = save_analysis(symbol, stock_data, analysis)
        except ValueError:
            pass
        except Exception as e:
            print(f"存储失败: {e}")

        return {
            "success": True,
            "data": {
                "stock_data": stock_data,
                "analysis": analysis,
                "record": record,
            },
        }
    except LLMServiceError as e:
        # LLM服务异常：可重试错误返回503，不可重试错误返回500
        status_code = 503 if e.retryable else 500
        raise HTTPException(status_code=status_code, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.get("/api/debug/llm")
def debug_llm():
    """测试LLM API连通性"""
    import httpx
    from config import LLM_API_KEY, LLM_API_BASE, LLM_MODEL

    if not LLM_API_KEY:
        return {"status": "error", "message": "LLM_API_KEY 未配置"}

    # 测试1: 网络连通性
    try:
        r = httpx.get(LLM_API_BASE.replace("/v4", ""), timeout=10)
        reachable = True
        status_code = r.status_code
    except Exception as e:
        reachable = False
        status_code = None
        net_error = str(e)

    # 测试2: 最小API调用
    try:
        client = _create_client()
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
            timeout=15.0,
        )
        api_ok = True
        api_response = resp.choices[0].message.content
    except Exception as e:
        api_ok = False
        api_response = None
        api_error = f"{type(e).__name__}: {e}"

    result = {
        "api_base": LLM_API_BASE,
        "model": LLM_MODEL,
        "key_set": bool(LLM_API_KEY),
        "key_prefix": LLM_API_KEY[:8] + "..." if LLM_API_KEY else None,
        "network": {"reachable": reachable, "status_code": status_code} if reachable else {"reachable": reachable, "error": net_error},
        "api_call": {"ok": True, "response": api_response} if api_ok else {"ok": False, "error": api_error},
    }
    return result


@app.get("/api/records")
def fetch_records(symbol: str = None, limit: int = 20):
    """获取历史分析记录"""
    try:
        records = get_analysis_records(symbol, limit)
        return {"success": True, "data": records}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记录失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
