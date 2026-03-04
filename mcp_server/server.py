# -*- coding: utf-8 -*-
"""Ashare MCP Server - FastMCP服务器主入口"""

from fastmcp import FastMCP
from mcp_server.config import MCP_SERVER_HOST, MCP_SERVER_PORT
from mcp_server.tools import get_stock_price, get_stock_latest

# 创建FastMCP服务器实例
mcp = FastMCP("ashare-stock-api")


# 注册get_stock_price工具
@mcp.tool()
def get_stock_price_tool(
    code: str,
    frequency: str = "1d",
    count: int = 10,
    end_date: str = ""
) -> dict:
    """获取A股股票行情数据

    说明：日线/周线/月线依赖新浪、腾讯接口，其日K多为 T+1 或收盘后更新，故最新一条常为前一交易日；需当日数据时可查分钟线（如 15m）或收盘后再查日线。

    Args:
        code: 股票代码 (支持: sh600519, sz000001, 600519.XSHG, 000001.XSHE, 600519.SH, 000001.SZ)
        frequency: K线周期 (1d/1w/1M/1m/5m/15m/30m/60m)
        count: 数据条数 (1-10000)
        end_date: 结束日期 (YYYY-MM-DD, 可选)

    Returns:
        JSON格式的股票行情数据，包含success、data和meta字段

    Examples:
        >>> get_stock_price_tool(code="sh600519", frequency="1d", count=5)
        >>> get_stock_price_tool(code="600519.SH", frequency="15m", count=10)
    """
    return get_stock_price(code, frequency, count, end_date)


@mcp.tool()
def get_stock_latest_tool(code: str) -> dict:
    """获取股票最新价格与最新交易日当日累计成交量

    Args:
        code: 股票代码 (支持: sh600519, sz000001, 600519.XSHG, 000001.XSHE, 600519.SH, 000001.SZ)

    Returns:
        JSON格式结果，包含:
        - data.latest_price: 最新一根1m K线收盘价
        - data.latest_volume: 最新交易日当日累计成交量（1m volume求和）
        - data.latest_kline_time: 最新1m K线时间
    """
    return get_stock_latest(code)


if __name__ == "__main__":
    # 启动MCP服务器
    mcp.run(transport="streamable-http", host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)
