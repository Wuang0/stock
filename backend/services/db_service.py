from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY


def get_supabase_client():
    """获取Supabase客户端"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase配置缺失，请检查环境变量")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def save_analysis(symbol: str, stock_data: dict, analysis: dict) -> dict:
    """保存分析结果到Supabase"""
    client = get_supabase_client()

    record = {
        "symbol": symbol,
        "stock_name": stock_data.get("name", symbol),
        "current_price": stock_data.get("current_price"),
        "change_pct": stock_data.get("change_pct"),
        "stock_data": stock_data,
        "summary": analysis.get("summary", ""),
        "sentiment": analysis.get("sentiment", "Neutral"),
        "risk_level": analysis.get("risk_level", "Medium"),
        "key_factors": analysis.get("key_factors", []),
        "recommendation": analysis.get("recommendation", ""),
    }

    result = client.table("analysis_records").insert(record).execute()
    return result.data[0] if result.data else record


def get_analysis_records(symbol: str = None, limit: int = 20) -> list:
    """获取历史分析记录"""
    client = get_supabase_client()

    query = client.table("analysis_records").select("*").order("created_at", desc=True).limit(limit)

    if symbol:
        query = query.eq("symbol", symbol)

    result = query.execute()
    return result.data
