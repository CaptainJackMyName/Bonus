"""Skill 插件模块"""

from bonus.skills.base import BaseSkill
from bonus.skills.fundamental_base import BaseFundamentalSkill
from bonus.skills.sina_skill import SinaSkill
from bonus.skills.tavily_skill import TavilySkill
from bonus.skills.akshare_skill import AkShareSkill
from bonus.skills.registry import load_skills, load_fundamental_skills

__all__ = [
    "BaseSkill",
    "BaseFundamentalSkill",
    "SinaSkill",
    "TavilySkill",
    "AkShareSkill",
    "load_skills",
    "load_fundamental_skills",
]
