import os
import json
import time
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
import logging
from functools import wraps
import random
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm_client")

class LLMClient:
    """统一的LLM API客户端，支持多种模型"""
    
    # 默认API基础URL
    DEFAULT_API_BASE = "https://openrouter.ai/api/v1"
    
    # 支持的模型列表
    SUPPORTED_MODELS = {
        "gpt-3.5-turbo": {
            "provider": "openai",
            "max_tokens": 4096,
            "supports_functions": True
        },
        "gpt-4": {
            "provider": "openai",
            "max_tokens": 8192,
            "supports_functions": True
        },
        "gpt-4-turbo": {
            "provider": "openai",
            "max_tokens": 128000,
            "supports_functions": True
        },
        "claude-3-sonnet-20240229": {
            "provider": "anthropic",
            "max_tokens": 200000,
            "supports_functions": True
        },
        "claude-3-opus-20240229": {
            "provider": "anthropic",
            "max_tokens": 200000,
            "supports_functions": True
        },
        "claude-3-haiku-20240307": {
            "provider": "anthropic",
            "max_tokens": 200000,
            "supports_functions": True
        },
        "meta-llama/llama-3-8b-instruct": {
            "provider": "meta",
            "max_tokens": 8192,
            "supports_functions": False
        },
        "meta-llama/llama-3-70b-instruct": {
            "provider": "meta",
            "max_tokens": 8192,
            "supports_functions": False
        },
        "mistralai/mixtral-8x7b-instruct": {
            "provider": "mistral",
            "max_tokens": 32768,
            "supports_functions": False
        },
        "google/gemini-1.5-pro": {
            "provider": "google",
            "max_tokens": 32768,
            "supports_functions": False
        }
    }
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 api_base: Optional[str] = None,
                 default_model: str = "openai/gpt-4o-mini",
                 timeout: int = 60,
                 max_retries: int = 3,
                 retry_delay: int = 2,
                 request_interval: float = 0.5):
        """初始化LLM客户端
        
        Args:
            api_key: API密钥，如果为None则从环境变量读取
            api_base: API基础URL，如果为None则使用默认值
            default_model: 默认使用的模型
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
            retry_delay: 重试间隔(秒)
            request_interval: 请求间隔(秒)，避免速率限制
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("API密钥未提供，请设置OPENROUTER_API_KEY环境变量或直接提供api_key参数")
        
        self.api_base = api_base or os.getenv("API_BASE", self.DEFAULT_API_BASE)
        self.default_model = default_model
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.request_interval = request_interval
        self.last_request_time = 0
        
        # 会话
        self._session = None
        
        logger.info(f"LLM客户端初始化完成，默认模型: {default_model}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建会话
        
        Returns:
            aiohttp.ClientSession: HTTP会话
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self._get_default_headers(),
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session
    
    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头
        
        Returns:
            Dict[str, str]: 默认请求头
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://silly-merchants.com"  # 可以替换为您的应用域名
        }
    
    def _handle_rate_limit(func: Callable) -> Callable:
        """处理速率限制的装饰器
        
        Args:
            func: 被装饰的函数
            
        Returns:
            Callable: 装饰后的函数
        """
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # 确保请求间隔
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.request_interval:
                await asyncio.sleep(self.request_interval - time_since_last)
            
            self.last_request_time = time.time()
            return await func(self, *args, **kwargs)
        
        return wrapper
    
    @_handle_rate_limit
    async def chat_completion(self, 
                           messages: List[Dict[str, str]],
                           model: Optional[str] = None,
                           temperature: float = 0.7,
                           max_tokens: Optional[int] = None,
                           top_p: float = 1.0,
                           functions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """发送聊天完成请求
        
        Args:
            messages: 消息列表
            model: 使用的模型，如果为None则使用默认模型
            temperature: 温度参数
            max_tokens: 最大生成token数
            top_p: top_p参数
            functions: 函数定义列表
            
        Returns:
            Dict: API响应
        """
        model = model or self.default_model
        
        if model not in self.SUPPORTED_MODELS:
            logger.warning(f"模型 {model} 不在支持列表中，可能无法正常工作")
        
        # 检查模型是否支持函数调用
        model_info = self.SUPPORTED_MODELS.get(model, {})
        if functions and not model_info.get("supports_functions", False):
            logger.warning(f"模型 {model} 不支持函数调用，将忽略函数参数")
            functions = None
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
        }
        
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        if functions:
            payload["functions"] = functions
            payload["function_call"] = "auto"
        
        url = f"{self.api_base}/chat/completions"
        
        for attempt in range(self.max_retries):
            try:
                session = await self._get_session()
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    
                    # 处理错误
                    error_text = await response.text()
                    logger.error(f"API请求失败 (尝试 {attempt+1}/{self.max_retries}): {response.status} - {error_text}")
                    
                    # 如果是速率限制错误，等待更长时间
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", self.retry_delay * 2))
                        await asyncio.sleep(retry_after)
                    else:
                        await asyncio.sleep(self.retry_delay)
            
            except Exception as e:
                logger.error(f"请求异常 (尝试 {attempt+1}/{self.max_retries}): {str(e)}")
                await asyncio.sleep(self.retry_delay)
        
        # 所有重试都失败
        raise Exception(f"API请求失败，已重试 {self.max_retries} 次")
    
    def extract_text_response(self, response: Dict[str, Any]) -> str:
        """从API响应中提取文本内容
        
        Args:
            response: API响应
            
        Returns:
            str: 提取的文本内容
        """
        try:
            choices = response.get("choices", [])
            if not choices:
                return ""
            
            message = choices[0].get("message", {})
            return message.get("content", "")
        
        except Exception as e:
            logger.error(f"提取响应文本时出错: {str(e)}")
            return ""
    
    def extract_function_call(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从API响应中提取函数调用
        
        Args:
            response: API响应
            
        Returns:
            Optional[Dict]: 函数调用信息，如果没有则为None
        """
        try:
            choices = response.get("choices", [])
            if not choices:
                return None
            
            message = choices[0].get("message", {})
            function_call = message.get("function_call")
            
            if not function_call:
                return None
            
            return {
                "name": function_call.get("name", ""),
                "arguments": json.loads(function_call.get("arguments", "{}"))
            }
        
        except Exception as e:
            logger.error(f"提取函数调用时出错: {str(e)}")
            return None
    
    async def close(self):
        """关闭会话"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

class PromptManager:
    """提示词管理器，用于加载和格式化提示词模板"""
    
    def __init__(self, prompt_dir: str = "prompts"):
        """初始化提示词管理器
        
        Args:
            prompt_dir: 提示词模板目录
        """
        self.prompt_dir = Path(prompt_dir)
        self.prompt_dir.mkdir(exist_ok=True)
        self.templates = {}
        
        # 加载所有提示词模板
        self._load_templates()
    
    def _load_templates(self):
        """加载所有提示词模板"""
        for template_file in self.prompt_dir.glob("*.txt"):
            try:
                with open(template_file, "r", encoding="utf-8") as f:
                    template_name = template_file.stem
                    self.templates[template_name] = f.read()
                logger.info(f"已加载提示词模板: {template_name}")
            except Exception as e:
                logger.error(f"加载提示词模板 {template_file} 失败: {str(e)}")
    
    def get_template(self, template_name: str) -> Optional[str]:
        """获取提示词模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            Optional[str]: 模板内容，如果不存在则为None
        """
        return self.templates.get(template_name)
    
    def format_prompt(self, template_name: str, **kwargs) -> Optional[str]:
        """格式化提示词模板
        
        Args:
            template_name: 模板名称
            **kwargs: 格式化参数
            
        Returns:
            Optional[str]: 格式化后的提示词，如果模板不存在则为None
        """
        template = self.get_template(template_name)
        if not template:
            logger.warning(f"提示词模板 {template_name} 不存在")
            return None
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"格式化提示词 {template_name} 时缺少参数: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"格式化提示词 {template_name} 失败: {str(e)}")
            return None

# 示例创建提示词模板
def create_example_templates():
    """创建示例提示词模板"""
    prompt_dir = Path("prompts")
    prompt_dir.mkdir(exist_ok=True)
    
    templates = {
        "system_prompt": (
            "你是一个游戏中的AI玩家，你的名字是{player_name}，性格特点：{personality}。\n"
            "游戏规则：{game_rules}\n\n"
            "请根据游戏情况做出最符合你性格的决策。"
        ),
        
        "persuasion_prompt": (
            "当前游戏状态：\n"
            "回合：{current_round}/{max_rounds}\n"
            "你的余额：{balance} 代币\n"
            "奖池：{prize_pool} 代币\n"
            "其他玩家：{other_players}\n\n"
            "你需要选择一名玩家进行说服，让他们向你转账。\n"
            "请选择目标玩家和说服金额，并提供有说服力的理由。\n\n"
            "输出格式：\n"
            "目标玩家：[玩家名称]\n"
            "说服金额：[金额]\n"
            "说服理由：[你的说服理由]"
        ),
        
        "item_use_prompt": (
            "当前游戏状态：\n"
            "回合：{current_round}/{max_rounds}\n"
            "你的余额：{balance} 代币\n"
            "你拥有的道具：{items}\n"
            "奖池：{prize_pool} 代币\n"
            "其他玩家：{other_players}\n\n"
            "现在是道具使用阶段，你可以选择使用一个道具。道具效果如下：\n"
            "{item_descriptions}\n\n"
            "请决定是否使用道具，如果使用，选择哪个道具以及目标玩家。\n\n"
            "输出格式：\n"
            "决定：[使用/不使用]\n"
            "道具：[道具名称，如果选择使用]\n"
            "目标：[目标玩家，如果需要]\n"
            "理由：[你的决策理由]"
        ),
        
        "purchase_prompt": (
            "当前游戏状态：\n"
            "回合：{current_round}/{max_rounds}\n"
            "你的余额：{balance} 代币\n"
            "你拥有的道具：{items}\n"
            "奖池：{prize_pool} 代币\n"
            "其他玩家：{other_players}\n\n"
            "现在是购买阶段，你可以选择购买一个道具。道具价格和效果如下：\n"
            "{item_descriptions}\n\n"
            "请决定是否购买道具，如果购买，选择哪个道具。\n\n"
            "输出格式：\n"
            "决定：[购买/不购买]\n"
            "道具：[道具名称，如果选择购买]\n"
            "理由：[你的决策理由]"
        )
    }
    
    for name, content in templates.items():
        template_path = prompt_dir / f"{name}.txt"
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"已创建示例提示词模板: {name}")

# 单例模式
_llm_client_instance = None
_prompt_manager_instance = None

def get_llm_client() -> LLMClient:
    """获取LLM客户端实例（单例模式）
    
    Returns:
        LLMClient: LLM客户端实例
    """
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance

def get_prompt_manager() -> PromptManager:
    """获取提示词管理器实例（单例模式）
    
    Returns:
        PromptManager: 提示词管理器实例
    """
    global _prompt_manager_instance
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptManager()
    return _prompt_manager_instance

# 示例用法
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # 创建示例提示词模板
        create_example_templates()
        
        # 获取LLM客户端
        client = get_llm_client()
        
        # 获取提示词管理器
        prompt_manager = get_prompt_manager()
        
        # 格式化提示词
        prompt = prompt_manager.format_prompt(
            "system_prompt",
            player_name="测试玩家",
            personality="谨慎且有策略",
            game_rules="这是一个多人说服游戏..."
        )
        
        # 发送聊天请求
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "游戏开始了，请介绍一下你自己"}
        ]
        
        try:
            response = await client.chat_completion(messages, temperature=0.7)
            text = client.extract_text_response(response)
            print(f"AI回复: {text}")
        except Exception as e:
            print(f"请求出错: {str(e)}")
        finally:
            await client.close()
    
    asyncio.run(test()) 