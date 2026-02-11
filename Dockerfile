# 使用Python 3.11官方镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY Ashare.py .
COPY mcp_server/ ./mcp_server/

# 安装Python依赖
RUN pip install --no-cache-dir -r mcp_server/requirements.txt

# 暴露端口
EXPOSE 3116

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3116/mcp').getcode() == 200 or exit(1)" || exit(1

# 启动MCP服务器
CMD ["python", "-m", "mcp_server.server"]
