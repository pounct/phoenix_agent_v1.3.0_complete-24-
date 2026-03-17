"""
Phoenix Agent v3 - Providers Module
====================================

MINIMAL PROVIDERS for First Operational Runtime.

Only 3 providers:
    - PlanningProvider: Decides what to do
    - LLMProvider: Calls LLM for reasoning
    - ToolProvider: Executes tools

No framework. Just providers.

Author: Phoenix Agent v3.2
"""

from .planning_provider import PlanningProvider
from .llm_provider import LLMProvider
from .tool_provider import ToolProvider, ToolRegistry

__all__ = [
    "PlanningProvider",
    "LLMProvider",
    "ToolProvider",
    "ToolRegistry",
]
