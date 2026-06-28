"""Skill 注册与加载"""

from typing import Dict

from bonus.skills.base import BaseSkill
from bonus.skills.fundamental_base import BaseFundamentalSkill
from bonus.skills.sina_skill import SinaSkill
from bonus.skills.tavily_skill import TavilySkill
from bonus.skills.akshare_skill import AkShareSkill
from bonus.utils.config import Config
from bonus.utils.logger import get_logger

logger = get_logger(__name__)


def load_skills(config: Config) -> Dict[str, BaseSkill]:
    """
    根据配置加载并注册所有启用的新闻信息源 Skill。

    Args:
        config: 应用配置对象

    Returns:
        Skill 名称到 Skill 实例的映射字典
    """
    skills: Dict[str, BaseSkill] = {}
    skills_config = config.skills_config

    # 新浪财经 Skill
    sina_cfg = skills_config.get("sina", {})
    if sina_cfg.get("enabled", False):
        skills["sina"] = SinaSkill(
            enabled=True,
            top_k=sina_cfg.get("top_k", 10),
        )
        logger.info("已注册 Skill: sina")

    # Tavily Skill
    tavily_cfg = skills_config.get("tavily", {})
    if tavily_cfg.get("enabled", False):
        api_key = tavily_cfg.get("api_key", "")
        if api_key:
            skills["tavily"] = TavilySkill(
                api_key=api_key,
                enabled=True,
                top_k=tavily_cfg.get("top_k", 10),
            )
            logger.info("已注册 Skill: tavily")
        else:
            logger.warning("Tavily Skill 已启用但 API Key 为空，跳过注册")

    # GroundAPI Skill（预留，使用 Tavily 类似逻辑）
    groundapi_cfg = skills_config.get("groundapi", {})
    if groundapi_cfg.get("enabled", False):
        logger.info("GroundAPI Skill 尚未实现，跳过")

    logger.info(f"共注册 {len(skills)} 个新闻 Skill: {list(skills.keys())}")
    return skills


def load_fundamental_skills(config: Config) -> Dict[str, BaseFundamentalSkill]:
    """
    根据配置加载并注册所有启用的基本面数据 Skill。

    Args:
        config: 应用配置对象

    Returns:
        Skill 名称到基本面 Skill 实例的映射字典
    """
    skills: Dict[str, BaseFundamentalSkill] = {}
    skills_config = config.skills_config

    # AkShare 基本面 Skill
    akshare_cfg = skills_config.get("akshare", {})
    if akshare_cfg.get("enabled", False):
        try:
            skills["akshare"] = AkShareSkill(
                enabled=True,
                recent_quarters=akshare_cfg.get("recent_quarters", 4),
            )
            logger.info("已注册基本面 Skill: akshare")
        except Exception as e:
            logger.error(f"注册 akshare Skill 失败: {e}")

    logger.info(f"共注册 {len(skills)} 个基本面 Skill: {list(skills.keys())}")
    return skills
