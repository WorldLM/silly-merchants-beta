#!/bin/bash
# 配置环境变量（根据实际情况修改）
export OPENROUTER_API_KEY=你的API密钥
export DEFAULT_MODEL=deepseek/deepseek-r1

# 启动服务器
echo "启动服务器..."
cd "$(dirname "$0")"
python3 -c "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8009, reload=True)" 