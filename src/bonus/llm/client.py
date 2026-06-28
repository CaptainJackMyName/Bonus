"""LLM 统一调用接口（基于 OpenAI 兼容 API）"""

import json
from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from bonus.utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """大语言模型客户端，封装 OpenAI 兼容接口"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str = "",
        temperature: float = 0.3,
        provider: str = "openai",
    ):
        if not api_key:
            logger.warning("LLM API Key 为空，LLM 功能将不可用")

        self.model = model
        self.temperature = temperature
        self.provider = provider

        client_kwargs: Dict[str, Any] = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = AsyncOpenAI(**client_kwargs)
        logger.info(f"LLM 客户端已初始化: provider={provider}, model={model}")

    @classmethod
    def from_config(cls, llm_config: Dict[str, Any]) -> "LLMClient":
        """从配置字典创建客户端"""
        return cls(
            api_key=llm_config.get("api_key", ""),
            model=llm_config.get("model", "gpt-4o"),
            base_url=llm_config.get("base_url", ""),
            temperature=llm_config.get("temperature", 0.3),
            provider=llm_config.get("provider", "openai"),
        )

    async def chat(
        self,
        user_prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
    ) -> str:
        """
        发送对话请求，返回文本响应。

        Args:
            user_prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 覆盖默认温度

        Returns:
            模型响应文本
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        logger.debug(f"LLM 请求: model={self.model}, messages={len(messages)}")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            timeout=180,
        )

        content = response.choices[0].message.content or ""
        logger.debug(f"LLM 响应长度: {len(content)} 字符")
        return content

    async def chat_json(
        self,
        user_prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
    ) -> Any:
        """
        发送对话请求并解析 JSON 响应。

        Returns:
            解析后的 JSON 对象
        """
        raw = await self.chat(user_prompt, system_prompt, temperature)
        return self._extract_json(raw)

    @staticmethod
    def _extract_json(text: str) -> Any:
        """从文本中提取 JSON（支持 markdown 代码块包裹）"""
        text = text.strip()

        # 去除 markdown 代码块
        if text.startswith("```"):
            lines = text.split("\n")
            # 移除首行 ```json 或 ```
            if lines[0].startswith("```"):
                lines = lines[1:]
            # 移除末尾 ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试找到第一个 { 和最后一个 } 之间的内容
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    pass
            logger.error(f"JSON 解析失败，原始文本: {text[:500]}")
            raise ValueError(f"无法从 LLM 响应中解析 JSON: {text[:200]}...")
