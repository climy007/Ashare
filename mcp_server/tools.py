# -*- coding: utf-8 -*-
"""MCP工具定义 - 股票行情查询"""

import re
import sys
import os
from pathlib import Path
from datetime import time

# 添加父目录到路径以导入Ashare
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from Ashare import get_price


def validate_stock_code(code: str) -> tuple[bool, str]:
    """验证股票代码格式

    Args:
        code: 股票代码

    Returns:
        (是否有效, 错误信息或标准化代码)
    """
    code = code.strip()
    patterns = [
        r'^sh\d{6}$',      # sh600519
        r'^sz\d{6}$',      # sz000001
        r'^\d{6}\.XSHG$',  # 600519.XSHG
        r'^\d{6}\.XSHE$',  # 000001.XSHE
        r'^\d{6}\.SH$',    # 600519.SH
        r'^\d{6}\.SZ$',    # 000001.SZ
    ]

    if not any(re.match(p, code, re.IGNORECASE) for p in patterns):
        return False, "Invalid stock code format. Expected formats: sh600519, sz000001, 600519.XSHG, 000001.XSHE, 600519.SH, 000001.SZ"

    return True, code


def normalize_stock_code(code: str) -> str:
    """将各种股票代码格式转换为Ashare支持的格式(sh/sz前缀)

    Args:
        code: 原始股票代码

    Returns:
        Ashare格式的股票代码
    """
    code = code.strip().upper()

    # 600519.SH -> sh600519
    match = re.match(r'^(\d{6})\.SH$', code)
    if match:
        return f"sh{match.group(1)}"

    # 000001.SZ -> sz000001
    match = re.match(r'^(\d{6})\.SZ$', code)
    if match:
        return f"sz{match.group(1)}"

    # 600519.XSHG -> sh600519
    match = re.match(r'^(\d{6})\.XSHG$', code)
    if match:
        return f"sh{match.group(1)}"

    # 000001.XSHE -> sz000001
    match = re.match(r'^(\d{6})\.XSHE$', code)
    if match:
        return f"sz{match.group(1)}"

    # 已经是sh600519或sz000001格式，直接返回
    return code.lower()


def validate_params(frequency: str, count: int) -> tuple[bool, str]:
    """验证频率和数量参数

    Args:
        frequency: K线周期
        count: 数据条数

    Returns:
        (是否有效, 错误信息)
    """
    valid_frequencies = ['1d', '1w', '1M', '1m', '5m', '15m', '30m', '60m']

    if frequency not in valid_frequencies:
        return False, f"Invalid frequency. Must be one of: {', '.join(valid_frequencies)}"

    if count < 1 or count > 10000:
        return False, "Count must be between 1 and 10000"

    return True, ""


def dataframe_to_ai_format(df, code: str, frequency: str, count: int) -> dict:
    """将Ashare的DataFrame转换为AI友好的JSON格式

    Args:
        df: Ashare返回的DataFrame
        code: 原始股票代码
        frequency: K线周期
        count: 数据条数

    Returns:
        JSON格式的股票数据
    """
    # 转换索引为ISO格式字符串
    data = []
    for index, row in df.iterrows():
        data.append({
            "date": index.isoformat(),
            "open": float(row['open']),
            "close": float(row['close']),
            "high": float(row['high']),
            "low": float(row['low']),
            "volume": float(row['volume'])
        })

    return {
        "success": True,
        "data": data,
        "meta": {
            "code": code,
            "frequency": frequency,
            "count": len(data),
            "fields": ["date", "open", "close", "high", "low", "volume"]
        }
    }


def error_response(message: str, details: str = "") -> dict:
    """返回统一的错误响应

    Args:
        message: 错误信息
        details: 详细信息

    Returns:
        标准错误响应格式
    """
    return {
        "success": False,
        "error": message,
        "details": details,
        "data": None
    }


def get_exchange_and_sessions(normalized_code: str) -> tuple[str, list[tuple[time, time]]]:
    """根据标准化代码识别交易所及交易时段"""
    # 当前仅处理A股主板/创业板常见交易时段，SSE/SZSE时段一致
    sessions = [
        (time(9, 30), time(11, 30)),
        (time(13, 0), time(15, 0)),
    ]

    if normalized_code.startswith("sh"):
        return "SSE", sessions
    if normalized_code.startswith("sz"):
        return "SZSE", sessions
    return "UNKNOWN", sessions


def filter_by_sessions(df, sessions: list[tuple[time, time]]):
    """按交易时段过滤DataFrame（基于索引时间）"""
    index_times = df.index.time
    mask = []
    for t in index_times:
        in_session = any(start <= t <= end for start, end in sessions)
        mask.append(in_session)
    return df[mask]


def get_stock_price(code: str, frequency: str = "1d", count: int = 10, end_date: str = "") -> dict:
    """获取A股股票行情数据

    Args:
        code: 股票代码 (支持: sh600519, sz000001, 600519.XSHG, 000001.XSHE, 600519.SH, 000001.SZ)
        frequency: K线周期 (1d/1w/1M/1m/5m/15m/30m/60m)
        count: 数据条数 (1-10000)
        end_date: 结束日期 (YYYY-MM-DD, 可选)

    Returns:
        JSON格式的股票行情数据
    """
    # 验证代码格式
    valid, result = validate_stock_code(code)
    if not valid:
        return error_response(result)

    # 验证参数
    valid, error_msg = validate_params(frequency, count)
    if not valid:
        return error_response(error_msg)

    # 转换为Ashare格式
    normalized_code = normalize_stock_code(code)

    try:
        # 调用Ashare接口
        df = get_price(normalized_code, frequency=frequency, count=count, end_date=end_date)
        return dataframe_to_ai_format(df, code, frequency, count)
    except Exception as e:
        return error_response(
            "Failed to fetch stock data",
            f"Error: {str(e)}. Please check the stock code and try again."
        )


def get_stock_latest(code: str) -> dict:
    """获取股票最新价格和当日累计成交量（基于1分钟K线）"""
    valid, result = validate_stock_code(code)
    if not valid:
        return error_response(result)

    normalized_code = normalize_stock_code(code)
    exchange, sessions = get_exchange_and_sessions(normalized_code)

    try:
        # 240 为A股常规全天分钟数，额外增加缓冲以提高兼容性
        df = get_price(normalized_code, frequency="1m", count=300)
    except Exception as e:
        return error_response(
            "Failed to fetch latest stock data",
            f"Error: {str(e)}. Please check the stock code and try again."
        )

    if df is None or df.empty:
        return error_response("No data", "No 1m kline data returned for this symbol.")

    # 仅聚合“最新交易日”的分钟数据
    latest_date = df.index[-1].date()
    latest_day_df = df[df.index.date == latest_date]
    if latest_day_df.empty:
        return error_response("No data", "No intraday data found for latest trading date.")

    # 自动识别交易时段后过滤，若过滤后为空则回退到最新交易日全量数据
    session_df = filter_by_sessions(latest_day_df, sessions)
    session_filter_applied = not session_df.empty
    active_df = session_df if session_filter_applied else latest_day_df

    latest_row = active_df.iloc[-1]
    latest_price = float(latest_row["close"])
    latest_volume = float(active_df["volume"].sum())
    latest_kline_time = active_df.index[-1].isoformat()

    return {
        # "success": True,
        # "data": {
        "code": code,
        # "exchange": exchange,
        "date": latest_date.isoformat(),
        "latest_kline_time": latest_kline_time,
        "latest_price": latest_price,
        "latest_volume": latest_volume
        # },
        # "meta": {
        #     "frequency": "1m",
        #     "volume_scope": "today_cumulative",
        #     "session_filter_applied": session_filter_applied,
        #     "sessions": ["09:30-11:30", "13:00-15:00"]
        # }
    }
