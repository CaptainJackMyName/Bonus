"""LLM 模块"""

from bonus.llm.client import LLMClient
from bonus.llm.prompts import (
    CAUSAL_CHAIN_PROMPT,
    DEEP_INFERENCE_PROMPT,
    CONFIRMATION_PROMPT,
    EVENT_EXTRACTION_PROMPT,
    FUNDAMENTAL_ANALYSIS_PROMPT,
)
from bonus.llm.parser import (
    parse_causal_chain_response,
    parse_deep_inference_response,
    parse_fundamental_assessment,
)

__all__ = [
    "LLMClient",
    "CAUSAL_CHAIN_PROMPT",
    "DEEP_INFERENCE_PROMPT",
    "CONFIRMATION_PROMPT",
    "EVENT_EXTRACTION_PROMPT",
    "FUNDAMENTAL_ANALYSIS_PROMPT",
    "parse_causal_chain_response",
    "parse_deep_inference_response",
    "parse_fundamental_assessment",
]
