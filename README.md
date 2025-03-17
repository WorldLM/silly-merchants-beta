# Silly Merchants Beta

一个基于AI的多人说服与交易游戏。

## 项目结构

```
silly-merchants-beta-main/
├── sillyworld-client/     # Next.js前端项目
├── sillyworld-server/     # Python FastAPI后端项目
├── README.md             # 项目说明文档
└── package.json          # 项目配置文件
```

## 快速开始

### 1. 环境要求

- Node.js 16+
- Python 3.8+
- npm 或 yarn

### 2. 后端配置

1. 进入后端目录：
```bash
cd sillyworld-server
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
创建 `.env` 文件并添加以下内容：
```
OPENROUTER_API_KEY=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
LOG_DIR=logs
PORT=8007
```

5. 启动后端服务：
```bash
python -m uvicorn main:app --reload --port 8007
```

### 3. 前端配置

1. 进入前端目录：
```bash
cd sillyworld-client
```

2. 安装依赖：
```bash
npm install
# 或
yarn install
```

3. 配置环境变量：
创建 `.env.local` 文件并添加：
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8007
```

4. 启动开发服务器：
```bash
npm run dev
# 或
yarn dev
```

## 游戏规则

1. 每个玩家初始获得固定数量的代币
2. 玩家可以购买道具：
   - 激进卡（15代币）：使用后若说服失败，将损失道具价格作为惩罚
   - 护盾卡（10代币）：使用后若被说服，支付金额减半
   - 情报卡（8代币）：可查看目标玩家的Prompt信息片段
   - 均富卡（12代币）：下一轮开始时与资金最多的玩家平分资金

3. 每轮游戏分为三个阶段：
   - 道具阶段：玩家可以使用道具
   - 说服阶段：玩家尝试说服其他玩家转账
   - 结算阶段：处理转账和道具效果

## 注意事项

1. 确保后端服务器在前端启动前已经运行
2. 默认后端端口为8007，前端端口为3000
3. 所有AI相关的功能都使用OpenRouter API，无需单独的OpenAI API key

## 问题排查

如果遇到端口占用问题，可以使用以下命令清理：

```bash
# Linux/Mac
pkill -9 -f "uvicorn"
pkill -9 -f "node"
pkill -9 -f "next"

# Windows
taskkill /F /IM "python.exe" /FI "WINDOWTITLE eq uvicorn*"
taskkill /F /IM "node.exe"
```

## 许可证

MIT License
