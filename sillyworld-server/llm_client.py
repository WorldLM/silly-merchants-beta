import os
import json
import time
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from pathlib import Path
import logging
from functools import wraps
import random
import re
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("llm_client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("llm_client")


class LLMClient:
    """统一的LLM API客户端，支持多种模型，增强错误处理和日志记录"""

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
        },
        # OpenRouter-specific models (prefixed format)
        "openai/gpt-4o": {
            "provider": "openai",
            "max_tokens": 128000,
            "supports_functions": True
        },
        "openai/gpt-4o-mini": {
            "provider": "openai",
            "max_tokens": 128000,
            "supports_functions": True
        },
        "anthropic/claude-3-opus": {
            "provider": "anthropic",
            "max_tokens": 200000,
            "supports_functions": True
        },
        "anthropic/claude-3-sonnet": {
            "provider": "anthropic",
            "max_tokens": 200000,
            "supports_functions": True
        },
        "anthropic/claude-3-haiku": {
            "provider": "anthropic",
            "max_tokens": 200000,
            "supports_functions": True
        }
    }

    def __init__(self,
                 api_key: Optional[str] = None,
                 api_base: Optional[str] = None,
                 default_model: str = "openai/gpt-4o-mini",
                 timeout: int = 60,
                 max_retries: int = 5,
                 retry_delay: int = 2,
                 request_interval: float = 0.5,
                 log_level: int = logging.INFO):
        """初始化LLM客户端
        
        Args:
            api_key: API密钥，如果为None则从环境变量读取
            api_base: API基础URL，如果为None则使用默认值
            default_model: 默认使用的模型
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
            retry_delay: 重试间隔(秒)
            request_interval: 请求间隔(秒)，避免速率限制
            log_level: 日志级别
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

        # Configure logging
        logger.setLevel(log_level)

        # 会话
        self._session = None

        # Statistics
        self.request_count = 0
        self.error_count = 0
        self.total_tokens = 0
        self.request_times = []

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
                              functions: Optional[List[Dict[str, Any]]] = None,
                              stream: bool = False) -> Dict[str, Any]:
        """发送聊天完成请求
        
        Args:
            messages: 消息列表
            model: 使用的模型，如果为None则使用默认模型
            temperature: 温度参数
            max_tokens: 最大生成token数
            top_p: top_p参数
            functions: 函数定义列表
            stream: 是否流式返回响应
            
        Returns:
            Dict: API响应
        """
        model = model or self.default_model
        start_time = time.time()
        self.request_count += 1

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
            "stream": stream
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        if functions:
            payload["functions"] = functions
            payload["function_call"] = "auto"

        url = f"{self.api_base}/chat/completions"

        logger.debug(f"Sending request to {url} with model {model}")

        try:
            response_data = await self._make_request_with_retry(url, payload)

            # Log tokens and update stats
            if response_data and "usage" in response_data:
                tokens = response_data["usage"].get("total_tokens", 0)
                self.total_tokens += tokens
                logger.debug(f"Request used {tokens} tokens, total: {self.total_tokens}")

            # Track request time
            request_time = time.time() - start_time
            self.request_times.append(request_time)
            logger.debug(f"Request completed in {request_time:.2f}s")

            return response_data

        except Exception as e:
            self.error_count += 1
            logger.error(f"请求异常，已重试 {self.max_retries} 次: {str(e)}")

            # Return a minimal fallback response
            return {
                "choices": [{
                    "message": {
                        "content": "I apologize, but I encountered an error processing your request. Please try again later.",
                        "role": "assistant"
                    },
                    "finish_reason": "error"
                }],
                "created": int(time.time()),
                "model": model,
                "error": str(e)
            }

    async def _make_request_with_retry(self, url, payload):
        """Make API request with retry logic
        
        Args:
            url: Request URL
            payload: Request payload
            
        Returns:
            Dict: API response
            
        Raises:
            Exception: If all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                session = await self._get_session()
                logger.debug(f"Attempt {attempt + 1}/{self.max_retries}")

                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return await response.json()

                    # 处理错误
                    error_text = await response.text()
                    logger.error(
                        f"API请求失败 (尝试 {attempt + 1}/{self.max_retries}): {response.status} - {error_text}")

                    # 如果是速率限制错误，等待更长时间
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", self.retry_delay * 2))
                        logger.warning(f"Rate limited, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                    else:
                        # Exponential backoff
                        backoff = (2 ** attempt) * self.retry_delay
                        jitter = random.uniform(0, 0.1 * backoff)
                        wait_time = backoff + jitter
                        logger.info(f"Retrying in {wait_time:.1f}s")
                        await asyncio.sleep(wait_time)

            except aiohttp.ClientError as e:
                logger.error(f"HTTP错误 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                await asyncio.sleep(self.retry_delay)

            except asyncio.TimeoutError:
                logger.error(f"请求超时 (尝试 {attempt + 1}/{self.max_retries})")
                await asyncio.sleep(self.retry_delay)

            except Exception as e:
                logger.error(f"意外错误 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
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
                logger.warning("没有choices在响应中")
                return ""

            message = choices[0].get("message", {})
            if not message:
                logger.warning("没有message在第一个choice中")
                return ""

            content = message.get("content")
            if content is None:
                logger.warning("content是None在message中")
                return ""

            return content.strip()

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
            if not message:
                return None

            function_call = message.get("function_call")
            if not function_call:
                return None

            # Parse arguments from string to dict
            arguments = function_call.get("arguments", "{}")
            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            return {
                "name": function_call.get("name"),
                "arguments": arguments
            }

        except Exception as e:
            logger.error(f"提取函数调用时出错: {str(e)}")
            return None

    def extract_reasoning_and_decision(self, content: str) -> Tuple[str, Dict[str, Any], str]:
        """提取思考过程、决策和公共消息
        
        Args:
            content: 完整响应内容
            
        Returns:
            Tuple[str, Dict[str, Any], str]: 思考过程、决策字典和公共消息
        """
        thinking = ""
        decision_dict = {"action_type": "wait"}
        public_message = ""

        try:
            # Extract thinking process using regex
            thinking_match = re.search(
                r"(?:Thinking Process:|思考过程:)(.*?)(?:Decision:|决策:|Public Message:|公开消息:)", content,
                re.DOTALL)
            if thinking_match:
                thinking = thinking_match.group(1).strip()

            # Extract decision parameters
            action_type_match = re.search(r"Action Type:\s*(\w+)", content)
            if action_type_match:
                decision_dict["action_type"] = action_type_match.group(1).strip().lower()

            target_match = re.search(r"Target Player:\s*([^\n]+)", content)
            if target_match:
                decision_dict["target_player"] = target_match.group(1).strip()

            amount_match = re.search(r"Amount:\s*(\d+)", content)
            if amount_match:
                decision_dict["amount"] = int(amount_match.group(1))

            item_type_match = re.search(r"Item Type:\s*([^\n]+)", content)
            if item_type_match:
                decision_dict["item_type"] = item_type_match.group(1).strip()

            # Extract public message
            public_match = re.search(r"(?:Public Message to All Players:|公开消息:)(.*?)(?:$)", content, re.DOTALL)
            if public_match:
                public_message = public_match.group(1).strip()

        except Exception as e:
            logger.error(f"解析AI响应时出错: {str(e)}")

        return thinking, decision_dict, public_message

    def parse_persuasion_evaluation(self, content: str) -> Tuple[bool, str, str]:
        """解析说服评估响应
        
        Args:
            content: 完整响应内容
            
        Returns:
            Tuple[bool, str, str]: 决策（接受/拒绝）、思考过程和响应消息
        """
        thinking = ""
        response_message = ""
        decision = False

        try:
            # Extract thinking process
            thinking_match = re.search(r"(?:Thinking Process:|思考过程:)(.*?)(?:Decision:|决策:|Response:|回应:|$)",
                                       content, re.DOTALL)
            if thinking_match:
                thinking = thinking_match.group(1).strip()

            # Extract decision (accept/reject)
            decision_match = re.search(r"Decision:\s*(Accept|Reject|接受|拒绝)", content, re.IGNORECASE)
            if decision_match:
                decision_text = decision_match.group(1).lower()
                decision = decision_text in ["accept", "接受"]

            # Extract response message
            response_match = re.search(r"(?:Response:|回应:)(.*?)(?:$)", content, re.DOTALL)
            if response_match:
                response_message = response_match.group(1).strip()

        except Exception as e:
            logger.error(f"解析说服评估时出错: {str(e)}")

        return decision, thinking, response_message

    def get_stats(self) -> Dict[str, Any]:
        """获取客户端使用统计
        
        Returns:
            Dict[str, Any]: 统计数据
        """
        avg_time = sum(self.request_times) / max(len(self.request_times), 1)
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "total_tokens": self.total_tokens,
            "average_request_time": avg_time,
            "success_rate": (self.request_count - self.error_count) / max(self.request_count, 1) * 100
        }

    async def close(self):
        """关闭会话"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("LLM客户端会话已关闭")


class PromptManager:
    """Prompt template manager for loading, formatting and tracking prompt usage"""

    def __init__(self, prompt_dir: str = "prompts"):
        """Initialize the prompt manager
        
        Args:
            prompt_dir: Directory containing prompt templates
        """
        self.prompt_dir = Path(prompt_dir)
        self.prompt_dir.mkdir(exist_ok=True)
        self.templates = {}
        self.last_modified = {}
        self.usage_stats = {}
        self.metrics = {
            "total_calls": 0,
            "formatting_errors": 0,
            "missing_templates": 0,
            "total_tokens": 0
        }

        # Load all templates
        self._load_templates()
        logger.info(f"Prompt manager initialized with {len(self.templates)} templates")

    def _load_templates(self):
        """Load all templates from the prompt directory"""
        for template_file in self.prompt_dir.glob("*.txt"):
            try:
                with open(template_file, "r", encoding="utf-8") as f:
                    template_name = template_file.stem
                    self.templates[template_name] = f.read()
                    self.last_modified[template_name] = template_file.stat().st_mtime
                    # Initialize usage stats for this template
                    if template_name not in self.usage_stats:
                        self.usage_stats[template_name] = {
                            "calls": 0,
                            "errors": 0,
                            "avg_tokens": 0,
                            "total_tokens": 0
                        }
                logger.info(f"Loaded prompt template: {template_name}")
            except Exception as e:
                logger.error(f"Failed to load template {template_file}: {str(e)}")

    def refresh_templates(self):
        """Refresh templates from disk, reloading only modified templates"""
        new_files = False
        for template_file in self.prompt_dir.glob("*.txt"):
            template_name = template_file.stem
            file_mtime = template_file.stat().st_mtime

            # Check if file is new or modified
            if template_name not in self.templates or file_mtime > self.last_modified.get(template_name, 0):
                try:
                    with open(template_file, "r", encoding="utf-8") as f:
                        self.templates[template_name] = f.read()
                        self.last_modified[template_name] = file_mtime

                        # Initialize usage stats if new
                        if template_name not in self.usage_stats:
                            self.usage_stats[template_name] = {
                                "calls": 0,
                                "errors": 0,
                                "avg_tokens": 0,
                                "total_tokens": 0
                            }

                        logger.info(f"Refreshed template: {template_name}")
                        new_files = True
                except Exception as e:
                    logger.error(f"Failed to refresh template {template_file}: {str(e)}")

        if not new_files:
            logger.debug("No template changes detected")

    def get_template(self, template_name: str) -> Optional[str]:
        """Get a template by name
        
        Args:
            template_name: Template name
            
        Returns:
            Optional[str]: Template content, or None if not found
        """
        if template_name not in self.templates:
            self.metrics["missing_templates"] += 1
            logger.warning(f"Template {template_name} not found")
            return None

        return self.templates.get(template_name)

    def format_prompt(self, template_name: str, **kwargs) -> Optional[str]:
        """Format a prompt template
        
        Args:
            template_name: Template name
            **kwargs: Format parameters
            
        Returns:
            Optional[str]: Formatted prompt, or None if template not found
        """
        self.metrics["total_calls"] += 1
        if template_name in self.usage_stats:
            self.usage_stats[template_name]["calls"] += 1

        template = self.get_template(template_name)
        if not template:
            return None

        try:
            formatted = template.format(**kwargs)

            # Approximate token count (very rough estimate)
            token_count = len(formatted.split()) + len(formatted) // 4

            # Update metrics
            self.metrics["total_tokens"] += token_count
            if template_name in self.usage_stats:
                stats = self.usage_stats[template_name]
                stats["total_tokens"] += token_count
                stats["avg_tokens"] = stats["total_tokens"] / stats["calls"]

            return formatted
        except KeyError as e:
            logger.error(f"Missing parameter in template {template_name}: {str(e)}")
            self.metrics["formatting_errors"] += 1
            if template_name in self.usage_stats:
                self.usage_stats[template_name]["errors"] += 1
            return None
        except Exception as e:
            logger.error(f"Error formatting template {template_name}: {str(e)}")
            self.metrics["formatting_errors"] += 1
            if template_name in self.usage_stats:
                self.usage_stats[template_name]["errors"] += 1
            return None

    def get_all_template_names(self) -> List[str]:
        """Get all available template names
        
        Returns:
            List[str]: List of template names
        """
        return list(self.templates.keys())

    def save_template(self, template_name: str, content: str) -> bool:
        """Save a template to disk
        
        Args:
            template_name: Template name
            content: Template content
            
        Returns:
            bool: True if successful
        """
        try:
            template_path = self.prompt_dir / f"{template_name}.txt"
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Update in-memory template
            self.templates[template_name] = content
            self.last_modified[template_name] = template_path.stat().st_mtime

            # Initialize usage stats if new
            if template_name not in self.usage_stats:
                self.usage_stats[template_name] = {
                    "calls": 0,
                    "errors": 0,
                    "avg_tokens": 0,
                    "total_tokens": 0
                }

            logger.info(f"Saved template: {template_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save template {template_name}: {str(e)}")
            return False

    def format_with_fallback(self,
                             primary_template: str,
                             fallback_template: str,
                             **kwargs) -> str:
        """Format prompt with fallback option if primary template fails
        
        Args:
            primary_template: Primary template name
            fallback_template: Fallback template name
            **kwargs: Format parameters
            
        Returns:
            str: Formatted prompt or error message if both fail
        """
        # Try primary template
        result = self.format_prompt(primary_template, **kwargs)
        if result:
            return result

        # Try fallback template
        logger.warning(f"Primary template {primary_template} failed, trying fallback {fallback_template}")
        result = self.format_prompt(fallback_template, **kwargs)
        if result:
            return result

        # Both failed
        logger.error(f"Both primary and fallback templates failed")
        return "Error: Failed to format prompt. Please check the logs."

    def get_stats(self) -> Dict[str, Any]:
        """Get template usage statistics
        
        Returns:
            Dict[str, Any]: Usage statistics
        """
        return {
            "metrics": self.metrics,
            "templates": self.usage_stats,
            "count": len(self.templates)
        }

    def reset_stats(self):
        """Reset usage statistics"""
        self.metrics = {
            "total_calls": 0,
            "formatting_errors": 0,
            "missing_templates": 0,
            "total_tokens": 0
        }

        for template_name in self.usage_stats:
            self.usage_stats[template_name] = {
                "calls": 0,
                "errors": 0,
                "avg_tokens": 0,
                "total_tokens": 0
            }

        logger.info("Prompt manager stats reset")


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
