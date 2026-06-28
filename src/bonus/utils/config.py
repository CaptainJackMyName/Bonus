"""配置加载与加密管理"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from bonus.utils.logger import get_logger

logger = get_logger(__name__)


class Config:
    """应用配置管理器"""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def get(self, *keys: str, default: Any = None) -> Any:
        """通过点分路径获取配置值，如 config.get('llm', 'api_key')"""
        current = self._data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    @property
    def raw(self) -> Dict[str, Any]:
        """返回原始配置字典"""
        return self._data

    @property
    def llm_config(self) -> Dict[str, Any]:
        return self._data.get("llm", {})

    @property
    def skills_config(self) -> Dict[str, Any]:
        return self._data.get("skills", {})

    @property
    def agent_config(self) -> Dict[str, Any]:
        return self._data.get("agent", {})

    @property
    def storage_config(self) -> Dict[str, Any]:
        return self._data.get("storage", {})

    @property
    def ui_config(self) -> Dict[str, Any]:
        return self._data.get("ui", {})

    def is_skill_enabled(self, skill_name: str) -> bool:
        """检查某个 Skill 是否启用"""
        skill_cfg = self.skills_config.get(skill_name, {})
        return skill_cfg.get("enabled", False)


def _get_default_config_path() -> Path:
    """获取默认配置文件路径"""
    return Path(__file__).parent.parent / "config.yaml"


def _get_user_config_path() -> Path:
    """获取用户配置文件路径（项目根目录下的 config.yaml）"""
    cwd = Path.cwd()
    for _ in range(4):
        candidate = cwd / "config.yaml"
        if candidate.exists():
            return candidate
        parent = cwd.parent
        if parent == cwd:
            break
        cwd = parent
    return Path.cwd() / "config.yaml"


def load_config(config_path: Optional[str] = None) -> Config:
    """
    加载配置文件。优先级：
    1. 显式指定的路径
    2. 环境变量 BONUS_CONFIG 指定的路径
    3. 当前工作目录下的 config.yaml
    4. 包内置的默认 config.yaml
    """
    if config_path:
        path = Path(config_path)
    elif env_path := os.environ.get("BONUS_CONFIG"):
        path = Path(env_path)
    else:
        user_path = _get_user_config_path()
        if user_path.exists():
            path = user_path
        else:
            path = _get_default_config_path()

    logger.info(f"加载配置文件: {path}")

    if not path.exists():
        logger.warning(f"配置文件不存在: {path}，使用默认配置")
        return Config(_default_config())

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    merged = _deep_merge(_default_config(), data)
    return Config(merged)


def _default_config() -> Dict[str, Any]:
    """返回默认配置"""
    return {
        "llm": {
            "provider": "openai",
            "api_key": "",
            "model": "gpt-4o",
            "base_url": "",
            "temperature": 0.3,
        },
        "skills": {
            "sina": {"enabled": True, "top_k": 10},
            "tavily": {"api_key": "", "enabled": False, "top_k": 10},
            "groundapi": {"api_key": "", "enabled": False, "top_k": 10},
            "akshare": {"enabled": True, "recent_quarters": 4},
        },
        "agent": {
            "default_mode": "auto",
            "max_inference_depth": 5,
            "min_confidence": 0.5,
        },
        "storage": {"db_path": "bonus.db", "max_history": 100},
        "ui": {"theme": "dark", "window_width": 1200, "window_height": 800},
    }


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """深度合并两个字典，override 优先"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
