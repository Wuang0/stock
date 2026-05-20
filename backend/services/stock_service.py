import baostock as bs
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta


def is_a_stock(symbol: str) -> bool:
    """判断是否为A股代码（纯6位数字，0/3/6开头）"""
    return symbol.isdigit() and len(symbol) == 6 and symbol[0] in ("0", "3", "6")


def _to_baostock_code(symbol: str) -> str:
    """转换为baostock代码格式: sh.603258 / sz.000001"""
    if symbol.startswith("6"):
        return f"sh.{symbol}"
    else:
        return f"sz.{symbol}"


def get_stock_data(symbol: str) -> dict:
    """获取股票行情数据，A股使用baostock，其他使用yfinance"""
    if is_a_stock(symbol):
        return _get_a_stock_data(symbol)
    else:
        return _get_yfinance_data(symbol)


def _get_a_stock_data(symbol: str) -> dict:
    """使用baostock获取A股数据"""
    bs_code = _to_baostock_code(symbol)
    lg = bs.login()
    if lg.error_code != "0":
        raise ConnectionError(f"baostock登录失败: {lg.error_msg}")

    try:
        # 获取近1年日K数据
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,open,high,low,close,volume,turn,peTTM",
            start_date=start_date,
            frequency="d",
            adjustflag="2",  # 前复权
        )

        if rs.error_code != "0":
            raise ValueError(f"未找到股票代码: {symbol} ({rs.error_msg})")

        rows = []
        while rs.next():
            rows.append(rs.get_row_data())

        if not rows:
            raise ValueError(f"未找到股票代码: {symbol}")

        df = pd.DataFrame(rows, columns=rs.fields)

        # 类型转换
        for col in ["open", "high", "low", "close", "volume", "turn", "peTTM"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # 近30个交易日
        hist = df.tail(30)
        latest = hist.iloc[-1]
        previous = hist.iloc[-2] if len(hist) > 1 else latest

        current_price = float(latest["close"])
        previous_close = float(previous["close"])
        change_pct = round((current_price - previous_close) / previous_close * 100, 2) if previous_close else 0

        price_history = []
        for _, row in hist.iterrows():
            price_history.append({
                "date": str(row["date"]),
                "open": round(float(row["open"]), 2),
                "high": round(float(row["high"]), 2),
                "low": round(float(row["low"]), 2),
                "close": round(float(row["close"]), 2),
                "volume": int(float(row["volume"])),
            })

        # 52周高低
        week_high_52 = round(float(df["high"].max()), 2)
        week_low_52 = round(float(df["low"].min()), 2)

        # 市盈率(TTM)直接从baostock获取
        pe_ratio = round(float(latest["peTTM"]), 2) if pd.notna(latest["peTTM"]) else None
        # 市值通过换手率反推：换手率(%) = 成交量/流通股本*100
        market_cap = None
        volume = float(latest["volume"]) if pd.notna(latest["volume"]) else 0
        turn = float(latest["turn"]) if pd.notna(latest["turn"]) else 0
        if turn > 0 and volume > 0:
            circulating_shares = volume / (turn / 100)
            market_cap = round(circulating_shares * current_price)

        return {
            "symbol": symbol,
            "name": symbol,
            "currency": "CNY",
            "current_price": round(current_price, 2),
            "previous_close": round(previous_close, 2),
            "change_pct": change_pct,
            "market_cap": market_cap,
            "pe_ratio": pe_ratio,
            "volume": int(volume),
            "day_high": round(float(latest["high"]), 2),
            "day_low": round(float(latest["low"]), 2),
            "52week_high": week_high_52,
            "52week_low": week_low_52,
            "price_history": price_history,
        }
    finally:
        bs.logout()


def _get_yfinance_data(symbol: str) -> dict:
    """使用yfinance获取非A股数据（美股、港股等）"""
    ticker = yf.Ticker(symbol)
    info = ticker.info
    hist = ticker.history(period="1mo")

    if hist.empty:
        raise ValueError(f"未找到股票代码: {symbol}")

    price_history = []
    for date, row in hist.iterrows():
        price_history.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
        })

    closes = hist["Close"].values
    change_pct = round(float((closes[-1] - closes[-2]) / closes[-2] * 100), 2) if len(closes) > 1 else 0

    return {
        "symbol": symbol,
        "name": info.get("shortName", symbol),
        "currency": info.get("currency", "USD"),
        "current_price": round(float(info.get("currentPrice") or closes[-1]), 2),
        "previous_close": round(float(info.get("previousClose") or (closes[-2] if len(closes) > 1 else closes[-1])), 2),
        "change_pct": change_pct,
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "volume": int(info.get("volume", 0) or 0),
        "day_high": round(float(info.get("dayHigh") or hist["High"].iloc[-1]), 2),
        "day_low": round(float(info.get("dayLow") or hist["Low"].iloc[-1]), 2),
        "52week_high": round(float(info.get("fiftyTwoWeekHigh") or 0), 2),
        "52week_low": round(float(info.get("fiftyTwoWeekLow") or 0), 2),
        "price_history": price_history,
    }
