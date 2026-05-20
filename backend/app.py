from typing import Optional
import os
import uuid
import threading
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

# 异步任务存储
_tasks: dict = {}


class AnalyzeRequest(BaseModel):
    symbol: str
    stock_data: Optional[dict] = None  # 前端传入已有的股票数据，避免重复请求


def _run_analysis(task_id: str, symbol: str, stock_data: dict | None):
    """后台线程执行分析"""
    try:
        if not stock_data:
            stock_data = get_stock_data(symbol)

        analysis = analyze_stock(stock_data)

        record = None
        try:
            record = save_analysis(symbol, stock_data, analysis)
        except ValueError:
            pass
        except Exception as e:
            print(f"存储失败: {e}")

        _tasks[task_id]["status"] = "done"
        _tasks[task_id]["result"] = {
            "stock_data": stock_data,
            "analysis": analysis,
            "record": record,
        }
    except Exception as e:
        _tasks[task_id]["status"] = "error"
        _tasks[task_id]["error"] = str(e)


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
    """提交分析任务，立即返回task_id，后台异步执行"""
    symbol = req.symbol.strip().upper()
    task_id = str(uuid.uuid4())
    _tasks[task_id] = {"status": "pending", "symbol": symbol}

    thread = threading.Thread(
        target=_run_analysis,
        args=(task_id, symbol, req.stock_data),
        daemon=True,
    )
    thread.start()

    return {"success": True, "task_id": task_id}


@app.get("/api/task/{task_id}")
def get_task(task_id: str):
    """轮询任务状态"""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = _tasks[task_id]
    if task["status"] == "done":
        return {"success": True, "status": "done", "data": task["result"]}
    elif task["status"] == "error":
        return {"success": False, "status": "error", "error": task["error"]}
    else:
        return {"success": True, "status": "pending"}


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
