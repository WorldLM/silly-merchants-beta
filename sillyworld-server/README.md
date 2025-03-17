# Silly Merchants 服务器端

这是Silly Merchants游戏的服务器端代码。Silly Merchants是一个多人AI说服与交易游戏，玩家需要通过说服、使用道具和策略规划来获取最多的代币。

## 主要功能

1. **游戏逻辑**
   - 多轮游戏机制
   - 道具系统
   - AI玩家逻辑
   - WebSocket实时通信

2. **游戏记录系统**
   - 完整游戏过程记录
   - JSON格式保存
   - 可读文本转换
   - 游戏摘要生成

3. **数据分析工具**
   - 玩家表现分析
   - 道具使用统计
   - 对决记录分析
   - 可视化图表生成

4. **多局测试框架**
   - 批量游戏测试
   - 随机玩家配置
   - 自动化报告
   - 效率和可靠性

5. **统一LLM接口**
   - 支持多种LLM模型
   - 统一API调用格式
   - 错误重试机制
   - 请求速率限制

6. **提示词工程**
   - 模板化提示词
   - 游戏场景适配
   - 个性化响应
   - 格式化输出

## 目录结构

- `game.py`: 游戏主逻辑
- `ai.py`: AI玩家逻辑
- `items.py`: 道具系统
- `models.py`: 数据模型
- `main.py`: API入口
- `websocket.py`: WebSocket服务
- `game_record.py`: 游戏记录系统
- `game_analyze.py`: 游戏分析工具
- `multi_game_runner.py`: 多局测试框架
- `llm_client.py`: 统一LLM接口
- `prompts/`: 提示词模板
- `logger.py`: 日志系统
- `exceptions.py`: 异常处理

## 使用方法

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

创建一个`.env`文件：

```
OPENROUTER_API_KEY=your_api_key_here
LOG_DIR=logs
PORT=8007
```

### 启动服务器

```bash
python -m uvicorn main:app --reload --port 8007
```

### 运行多局测试

```bash
python multi_game_runner.py -n 10
```

## 数据分析

游戏完成后，可以使用以下命令分析结果：

```bash
python game_analyze.py
```

分析报告将保存在`analysis_results`目录中。

## 游戏参数

- **默认初始余额**: 100代币
- **默认最大回合数**: 8回合
- **道具价格**:
  - 激进卡: 15代币
  - 护盾卡: 10代币
  - 情报卡: 8代币
  - 均富卡: 12代币 