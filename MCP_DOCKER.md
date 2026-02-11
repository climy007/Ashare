# Ashare MCP Server - Docker部署指南

使用Docker快速部署Ashare MCP服务器。

## 快速启动

### 使用Docker Compose（推荐）

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f ashare-mcp

# 停止服务
docker-compose down
```

### 使用Docker命令

```bash
# 构建镜像
docker build -t ashare-mcp:latest .

# 运行容器
docker run -d \
  --name ashare-mcp \
  -p 3116:3116 \
  ashare-mcp:latest

# 查看日志
docker logs -f ashare-mcp

# 停止容器
docker stop ashare-mcp
```

## 配置

### 环境变量

| 变量名 | 默认值 | 说明 |
|---------|---------|------|
| `MCP_SERVER_HOST` | `0.0.0.0` | 服务器监听地址 |
| `MCP_SERVER_PORT` | `3116` | 服务器监听端口 |

### 自定义配置

```bash
# 使用自定义端口
docker run -d \
  --name ashare-mcp \
  -p 8080:3116 \
  ashare-mcp:latest

# 使用环境变量
docker run -d \
  --name ashare-mcp \
  -p 3116:3116 \
  -e MCP_SERVER_PORT=3116 \
  ashare-mcp:latest
```

## 访问服务

服务启动后，MCP服务器将在以下地址可用：

```
http://localhost:3116/mcp
```

### MCP客户端配置

```json
{
  "mcpServers": {
    "ashare": {
      "url": "http://localhost:3116/mcp",
      "transport": "streamable-http"
    }
  }
}
```

## API测试

```bash
# 测试服务是否运行
curl http://localhost:3116/mcp

# 列出可用工具（需要sessionId）
curl -X POST "http://localhost:3116/mcp?sessionId=test" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

## 健康检查

容器包含健康检查，每30秒检查一次服务状态：

```bash
# 检查容器健康状态
docker ps
docker inspect --format='{{.State.Health.Status}}' ashare-mcp
```

## 故障排查

### 查看日志

```bash
# Docker Compose
docker-compose logs ashare-mcp

# Docker命令
docker logs ashare-mcp
```

### 进入容器调试

```bash
docker exec -it ashare-mcp bash
```

### 端口冲突

如果3116端口已被占用，可以映射到其他端口：

```bash
docker run -d \
  --name ashare-mcp \
  -p 8080:3116 \
  ashare-mcp:latest
```

## 生产环境建议

1. **使用固定版本标签**
   ```bash
   docker build -t ashare-mcp:v1.0.0 .
   docker run -d --name ashare-mcp ashare-mcp:v1.0.0
   ```

2. **配置资源限制**
   ```yaml
   services:
     ashare-mcp:
       deploy:
         resources:
           limits:
             cpus: '0.5'
             memory: 512M
   ```

3. **使用外部网络**
   ```yaml
   services:
     ashare-mcp:
       networks:
         - external-network
   networks:
     external-network:
       external: true
   ```

4. **配置日志轮转**
   ```yaml
   services:
     ashare-mcp:
       logging:
         driver: "json-file"
         options:
           max-size: "10m"
           max-file: "3"
   ```
