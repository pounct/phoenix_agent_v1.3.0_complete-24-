"""
Phoenix Agent v3 - Planning Provider
=====================================

THE DECISION MAKER.

PlanningProvider analyzes the user request and decides:
    - What capability is needed
    - What parameters to pass
    - Whether to use tools or LLM

SIMPLE. NO FRAMEWORK. JUST LOGIC.

Author: Phoenix Agent v3.2
"""

import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

import sys
sys.path.insert(0, '/home/z/my-project')

from phoenix_agent.v3.runtime.task import Task, ProviderResult
from phoenix_agent.v3.runtime.provider_contract import BaseProvider


@dataclass
class Plan:
    """Simple plan structure."""
    action: str  # "tool" or "llm"
    tool_name: Optional[str] = None
    prompt: Optional[str] = None
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class PlanningProvider(BaseProvider):
    """
    THE PLANNING PROVIDER.
    
    Decides what to do with user input.
    
    Simple pattern matching for now.
    Can be enhanced with LLM-based planning later.
    """
    
    # Tool patterns: regex -> (tool_name, extractor)
    TOOL_PATTERNS = {
        r"count words? (in|of)?:?\s*(.+)": "word_count",
        r"how many words? (in|of)?:?\s*(.+)": "word_count",
        r"summarize:?\s*(.+)": "summarize",
        r"summary of:?\s*(.+)": "summarize",
        r"make (it |this )?shorter:?\s*(.+)": "summarize",
        r"reverse:?\s*(.+)": "reverse",
        r"uppercase:?\s*(.+)": "uppercase",
        r"lowercase:?\s*(.+)": "lowercase",
        r"calculate:?\s*(.+)": "calculate",
        r"compute:?\s*(.+)": "calculate",
    }
    
    # LLM patterns: questions needing reasoning
    LLM_PATTERNS = {
        r"why .+\?": "reasoning",
        r"explain .+": "explanation",
        r"what is .+\?": "definition",
        r"how (do|does|can|to) .+\?": "how_to",
        r"compare .+": "comparison",
    }
    
    def __init__(self):
        super().__init__(
            name="planning_provider",
            capability="planning",
            cost=0.0,  # Planning is free
            latency_ms=1,
            reliability=1.0,
            priority=10
        )
        self.plans_created = 0
    
    async def execute(self, task: Task) -> ProviderResult:
        """
        Analyze task and create a plan.
        
        Input (task.input):
            - "query": User's request string
        
        Output (result.data):
            - "plan": Plan object with action, tool_name, parameters
        """
        query = task.input.get("query", "")
        
        if not query:
            return ProviderResult.fail(
                error="No query provided",
                provider=self._metadata.name
            )
        
        # Try to match tool patterns first
        plan = self._match_tool_pattern(query)
        
        if plan:
            self.plans_created += 1
            return ProviderResult.ok(
                data={
                    "plan": {
                        "action": plan.action,
                        "tool_name": plan.tool_name,
                        "prompt": plan.prompt,
                        "parameters": plan.parameters
                    }
                },
                provider=self._metadata.name
            )
        
        # Try to match LLM patterns
        plan = self._match_llm_pattern(query)
        
        if plan:
            self.plans_created += 1
            return ProviderResult.ok(
                data={
                    "plan": {
                        "action": plan.action,
                        "prompt": plan.prompt,
                        "parameters": plan.parameters or {}
                    }
                },
                provider=self._metadata.name
            )
        
        # Default: use LLM for general questions
        self.plans_created += 1
        return ProviderResult.ok(
            data={
                "plan": {
                    "action": "llm",
                    "prompt": query,
                    "parameters": {}
                }
            },
            provider=self._metadata.name
        )
    
    def _match_tool_pattern(self, query: str) -> Optional[Plan]:
        """Match query against tool patterns."""
        query_lower = query.lower().strip()
        
        for pattern, tool_name in self.TOOL_PATTERNS.items():
            match = re.match(pattern, query_lower, re.IGNORECASE)
            if match:
                # Extract the text from the last capture group
                groups = match.groups()
                text = groups[-1] if groups else ""
                
                return Plan(
                    action="tool",
                    tool_name=tool_name,
                    parameters={"text": text.strip()}
                )
        
        return None
    
    def _match_llm_pattern(self, query: str) -> Optional[Plan]:
        """Match query against LLM patterns."""
        query_lower = query.lower().strip()
        
        for pattern, reasoning_type in self.LLM_PATTERNS.items():
            if re.match(pattern, query_lower, re.IGNORECASE):
                return Plan(
                    action="llm",
                    prompt=query,
                    parameters={"reasoning_type": reasoning_type}
                )
        
        return None


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def create_plan(query: str) -> Plan:
    """
    Synchronous helper to create a plan.
    
    Usage:
        plan = create_plan("count words in hello world")
        # plan.action = "tool"
        # plan.tool_name = "word_count"
    """
    provider = PlanningProvider()
    
    # Simple synchronous matching
    query_lower = query.lower().strip()
    
    for pattern, tool_name in PlanningProvider.TOOL_PATTERNS.items():
        match = re.match(pattern, query_lower, re.IGNORECASE)
        if match:
            groups = match.groups()
            text = groups[-1] if groups else ""
            return Plan(
                action="tool",
                tool_name=tool_name,
                parameters={"text": text.strip()}
            )
    
    # Default to LLM
    return Plan(
        action="llm",
        prompt=query,
        parameters={}
    )


# ==========================================
# EXPORTS
# ==========================================

__all__ = ["PlanningProvider", "Plan", "create_plan"]