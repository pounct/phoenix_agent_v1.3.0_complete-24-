"""
Phoenix Agent v3 - Minimal Agent
=================================

THE FIRST OPERATIONAL RUNTIME.

Phoenix can now DO things, not just run tests.

Simple interface:
    result = await phoenix.run("count words in hello world")
    result = await phoenix.run("summarize: This is a long text...")
    result = await phoenix.run("What is AI?")

Author: Phoenix Agent v3.2
"""

import asyncio
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass

import sys
sys.path.insert(0, '/home/z/my-project')

from phoenix_agent.v3.runtime.task import Task, TaskState, ProviderResult, TaskResult
from phoenix_agent.v3.runtime.router import Router, ProviderRegistry
from phoenix_agent.v3.runtime.execution_loop import ExecutionLoop, LoopConfig
from phoenix_agent.v3.runtime.metrics import create_collector, MetricsCollector

from phoenix_agent.providers.tool_provider import ToolProvider, ToolRegistry, execute_tool
from phoenix_agent.providers.llm_provider import LLMProvider, ask_llm
from phoenix_agent.providers.planning_provider import PlanningProvider, create_plan


# ==========================================
# PHOENIX RESULT
# ==========================================

@dataclass
class PhoenixResult:
    """Result from Phoenix agent execution."""
    success: bool
    response: str
    action: str  # "tool" or "llm"
    tool_name: Optional[str] = None
    data: Dict[str, Any] = None
    trace: list = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.trace is None:
            self.trace = []
    
    def __str__(self) -> str:
        return self.response
    
    def __repr__(self) -> str:
        return f"PhoenixResult(success={self.success}, action={self.action}, response='{self.response[:50]}...')"


# ==========================================
# PHOENIX AGENT
# ==========================================

class Phoenix:
    """
    THE PHOENIX AGENT.
    
    Minimal operational agent.
    
    Usage:
        phoenix = Phoenix()
        
        # Simple requests
        result = await phoenix.run("count words in hello world")
        print(result.response)  # "Word count: 2"
        
        result = await phoenix.run("What is AI?")
        print(result.response)  # LLM response
    
    Features:
        - Planning: Analyzes request, decides action
        - Tools: word_count, summarize, reverse, etc.
        - LLM: Mock responses (can connect to real LLM)
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        llm_mode: str = "mock"
    ):
        """
        Initialize Phoenix agent.
        
        Args:
            config: Optional configuration
            llm_mode: "mock" for testing, "api" for real LLM
        """
        self.config = config or {}
        
        # Create providers
        self.planning_provider = PlanningProvider()
        self.tool_provider = ToolProvider()
        self.llm_provider = LLMProvider(mode=llm_mode)
        
        # Create registry and register providers
        self.registry = ProviderRegistry()
        self.registry.register(self.planning_provider)
        self.registry.register(self.tool_provider)
        self.registry.register(self.llm_provider)
        
        # Create router and loop
        self.router = Router(self.registry)
        self.loop = ExecutionLoop(
            self.router,
            LoopConfig(max_queue_size=100)
        )
        
        # Metrics
        self.metrics = create_collector()
        
        # Stats
        self.total_requests = 0
        self.successful_requests = 0
    
    async def run(self, query: str) -> PhoenixResult:
        """
        Run a query through Phoenix.
        
        This is the main entry point.
        
        Args:
            query: User's request string
            
        Returns:
            PhoenixResult with response and metadata
        """
        self.total_requests += 1
        trace = []
        
        try:
            # Step 1: Plan
            trace.append({"step": "planning", "query": query})
            plan = create_plan(query)
            
            # Step 2: Execute based on plan
            if plan.action == "tool":
                result = await self._execute_tool(plan, trace)
            else:
                result = await self._execute_llm(query, plan, trace)
            
            self.successful_requests += 1
            self.metrics.record_task_completion(
                task_id=f"req_{self.total_requests}",
                duration_ms=0,  # Will be filled by result
                success=True
            )
            
            return result
        
        except Exception as e:
            return PhoenixResult(
                success=False,
                response=f"Error: {e}",
                action="error",
                trace=trace
            )
    
    async def _execute_tool(self, plan, trace: list) -> PhoenixResult:
        """Execute a tool based on plan."""
        tool_name = plan.tool_name
        parameters = plan.parameters or {}
        
        trace.append({
            "step": "tool_execution",
            "tool": tool_name,
            "parameters": parameters
        })
        
        # Execute tool
        tool_result = execute_tool(tool_name, **parameters)
        
        # Format response based on tool
        response = self._format_tool_response(tool_name, tool_result)
        
        return PhoenixResult(
            success=True,
            response=response,
            action="tool",
            tool_name=tool_name,
            data=tool_result,
            trace=trace
        )
    
    async def _execute_llm(self, query: str, plan, trace: list) -> PhoenixResult:
        """Execute LLM reasoning."""
        trace.append({
            "step": "llm_execution",
            "prompt": query
        })
        
        # Call LLM
        response = await ask_llm(query)
        
        return PhoenixResult(
            success=True,
            response=response,
            action="llm",
            data={"prompt": query, "response": response},
            trace=trace
        )
    
    def _format_tool_response(self, tool_name: str, result: Dict[str, Any]) -> str:
        """Format tool result as human-readable response."""
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        formatters = {
            "word_count": lambda r: f"Word count: {r['count']}",
            "character_count": lambda r: f"Character count: {r['count']} (no spaces: {r['count_no_spaces']})",
            "summarize": lambda r: f"Summary: {r['summary']}",
            "reverse": lambda r: f"Reversed: {r['reversed']}",
            "uppercase": lambda r: f"Uppercase: {r['uppercase']}",
            "lowercase": lambda r: f"Lowercase: {r['lowercase']}",
            "calculate": lambda r: r.get('formatted', f"Result: {r.get('result', 'N/A')}"),
        }
        
        formatter = formatters.get(tool_name, lambda r: str(r))
        return formatter(result)
    
    # ==========================================
    # CONVENIENCE METHODS
    # ==========================================
    
    async def word_count(self, text: str) -> int:
        """Count words in text."""
        result = await self.run(f"count words in {text}")
        return result.data.get("count", 0) if result.success else 0
    
    async def summarize(self, text: str) -> str:
        """Summarize text."""
        result = await self.run(f"summarize: {text}")
        return result.response if result.success else ""
    
    async def ask(self, question: str) -> str:
        """Ask a question (LLM)."""
        result = await self.run(question)
        return result.response if result.success else ""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "success_rate": self.successful_requests / max(1, self.total_requests),
            "planning_calls": self.planning_provider.plans_created,
            "tool_calls": self.tool_provider.executions,
            "llm_calls": self.llm_provider.calls,
        }


# ==========================================
# MODULE-LEVEL INSTANCE
# ==========================================

# Create default instance for convenience
_default_phoenix = None


def get_phoenix() -> Phoenix:
    """Get or create default Phoenix instance."""
    global _default_phoenix
    if _default_phoenix is None:
        _default_phoenix = Phoenix()
    return _default_phoenix


async def run(query: str) -> PhoenixResult:
    """
    Quick run function.
    
    Usage:
        from phoenix_agent.v3.agent import run
        result = await run("count words in hello world")
    """
    phoenix = get_phoenix()
    return await phoenix.run(query)


# ==========================================
# EXPORTS
# ==========================================

__all__ = [
    "Phoenix",
    "PhoenixResult",
    "get_phoenix",
    "run",
]
