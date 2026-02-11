# Ashare MCP Server 设计文档

## 概述

将Ashare股票行情接口封装为MCP (Model Context Protocol) 服务，使用FastMCP框架和streamable-http传输协议，为AI助手提供A股实时行情数据查询能力。

## 项目结构

```
Ashare/
├── Ashare.py              # 原有代码（保持不变）
├── mcp_server/
│   ├── __init__.py
│   ├── server.py          # MCP服务器主入口
│   ├── tools.py           # MCP工具定义
│   ├── requirements.txt   # 依赖项
│   └── config.py          # 配置文件
└── docs/plans/
    └── 2025-02-11-mcp-server-design.md
```

## MCP工具定义

### get_stock_price

获取A股股票行情数据的核心工具。

**参数**:
- `code` (string, required): 股票代码
  - 支持格式: sh600519, sz000001, 600519.XSHG, 000001.XSHE, 600519.SH, 000001.SZ
- `frequency` (string, default="1d"): K线周期
  - 日线: 1d
  - 周线: 1w
  - 月线: 1M
  - 分钟线: 1m, 5m, 15m, 30m, 60m
- `count` (integer, default=10): 获取数据条数 (1-10000)
- `end_date` (string, optional): 结束日期，格式YYYY-MM-DD

**返回格式**:
```json
{
  "success": true,
  "data": [
    {
      "date": "2024-01-15T09:30:00",
      "open": 100.5,
      "close": 102.3,
      "high": 103.0,
      "low": 100.0,
      "volume": 1234567.0
    }
  ],
  "meta": {
    "code": "sh600519",
    "frequency": "1d",
    "count": 10,
    "fields": ["date", "open", "close", "high", "low", "volume"]
  }
}
```

**错误响应格式**:
```json
{
  "success": false,
  "error": "错误描述",
  "details": "详细信息",
  "data": null
}
```

## 服务器实现

### 技术栈
- FastMCP: MCP服务器框架
- uvicorn: ASGI服务器（FastMCP依赖）
- pandas: 数据处理（Ashare依赖）
- requests: HTTP客户端（Ashare依赖）

### 核心组件

**server.py**:
```python
from fastmcp import FastMCP
from mcp_server.config import MCP_SERVER_HOST, MCP_SERVER_PORT
from mcp_server.tools import get_stock_price

mcp = FastMCP("ashare-stock-api")

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)
```

**config.py**:
```python
MCP_SERVER_HOST = "0.0.0.0"
MCP_SERVER_PORT = 8000
```

### 启动方式
```bash
# 启动HTTP服务器
python -m mcp_server.server
```

## 数据转换逻辑

### dataframe_to_ai_format
将Ashare的DataFrame转换为AI友好的JSON格式：
- 转换DatetimeIndex为ISO 8601字符串格式
- 确保所有数值为float类型
- 保持数据完整性，添加元数据信息

### normalize_stock_code
将各种股票代码格式统一转换为Ashare支持的格式：
- 600519.SH → sh600519
- 000001.SZ → sz000001
- 600519.XSHG → sh600519
- 000001.XSHE → sz000001
- sh600519 → sh600519 (不变)

## 错误处理

### 验证层级

1. **股票代码验证**:
   - 格式正则匹配
   - 返回友好的错误提示

2. **参数验证**:
   - frequency: 必须为有效值
   - count: 1-10000范围

3. **异常处理**:
   - 参数验证 → 400错误，明确提示
   - 网络请求失败 → 503错误，包含重试建议
   - 数据解析失败 → 500错误，记录详细日志

## 客户端使用

### MCP客户端配置

```json
{
  "mcpServers": {
    "ashare": {
      "url": "http://localhost:8000/mcp",
      "transport": "streamable-http"
    }
  }
}
```

### 使用场景示例

**查询股票行情**:
```
用户: 查询贵州茅台最近10天的日线行情
助手: [调用 get_stock_price(code="sh600519", frequency="1d", count=10)]
```

**对比分析**:
```
用户: 对比上证指数和深证成指的周线走势
助手: [并行调用]
     - get_stock_price(code="sh000001", frequency="1w", count=20)
     - get_stock_price(code="sz399006", frequency="1w", count=20)
```

**实时行情**:
```
用户: 获取平安银行15分钟级别的实时行情
助手: [调用 get_stock_price(code="sz000001", frequency="15m", count=5)]
```

### HTTP API调用

```bash
curl -X POST http://localhost:8000/mcp/tools/get_stock_price \
  -H "Content-Type: application/json" \
  -d '{
    "code": "600519.SH",
    "frequency": "1d",
    "count": 5
  }'
```

## 依赖项

### requirements.txt
```
fastmcp>=0.1.0
pandas>=1.0.0
requests>=2.20.0
```

## 设计原则

1. **最小化侵入**: 不修改Ashare原有代码
2. **格式兼容**: 支持多种股票代码格式
3. **AI友好**: 返回结构化、易解析的JSON数据
4. **错误友好**: 提供清晰的错误信息和处理建议
5. **灵活部署**: 支持HTTP服务模式，易于扩展

## 未来扩展

- 批量查询多只股票
- 添加技术指标计算工具
- 支持股票代码模糊搜索
- 添加实时行情推送功能
