"""
Phoenix Agent v3 - Tool Provider
=================================

THE EXECUTOR.

ToolProvider executes tools:
    - word_count: Count words in text
    - summarize: Simple text summary
    - reverse: Reverse text
    - uppercase/lowercase: Transform text
    - calculate: Simple math

SIMPLE. NO FRAMEWORK. JUST TOOLS.

Author: Phoenix Agent v3.2
"""

import re
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass

import sys
sys.path.insert(0, '/home/z/my-project')

from phoenix_agent.v3.runtime.task import Task, ProviderResult
from phoenix_agent.v3.runtime.provider_contract import BaseProvider


# ==========================================
# TOOL DEFINITIONS
# ==========================================

@dataclass
class Tool:
    """Simple tool definition."""
    name: str
    description: str
    execute: Callable[[Dict[str, Any]], Dict[str, Any]]


# ==========================================
# BUILT-IN TOOLS
# ==========================================

def tool_word_count(params: Dict[str, Any]) -> Dict[str, Any]:
    """Count words in text."""
    text = params.get("text", "")
    words = text.split()
    return {
        "count": len(words),
        "text": text,
        "words": words
    }


def tool_summarize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simple text summarization (first sentence + word count)."""
    text = params.get("text", "")
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return {"summary": "", "method": "empty"}
    
    # Simple summary: first sentence + stats
    first_sentence = sentences[0]
    word_count = len(text.split())
    sentence_count = len(sentences)
    
    summary = first_sentence
    if len(sentences) > 1:
        summary += f"... ({sentence_count} sentences, {word_count} words total)"
    
    return {
        "summary": summary,
        "sentence_count": sentence_count,
        "word_count": word_count,
        "method": "first_sentence"
    }


def tool_reverse(params: Dict[str, Any]) -> Dict[str, Any]:
    """Reverse text."""
    text = params.get("text", "")
    return {
        "reversed": text[::-1],
        "original": text
    }


def tool_uppercase(params: Dict[str, Any]) -> Dict[str, Any]:
    """Convert to uppercase."""
    text = params.get("text", "")
    return {
        "uppercase": text.upper(),
        "original": text
    }


def tool_lowercase(params: Dict[str, Any]) -> Dict[str, Any]:
    """Convert to lowercase."""
    text = params.get("text", "")
    return {
        "lowercase": text.lower(),
        "original": text
    }


def tool_calculate(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simple calculation (safe eval for basic math)."""
    text = params.get("text", "")
    
    # Extract mathematical expression
    # Only allow numbers, operators, and basic math
    allowed = set("0123456789+-*/.() ")
    expr = "".join(c for c in text if c in allowed)
    
    if not expr:
        return {"error": "No valid expression found", "expression": text}
    
    try:
        # Safe evaluation of simple math
        result = eval(expr, {"__builtins__": {}}, {})
        return {
            "result": result,
            "expression": expr,
            "formatted": f"{expr} = {result}"
        }
    except Exception as e:
        return {
            "error": str(e),
            "expression": expr
        }


def tool_character_count(params: Dict[str, Any]) -> Dict[str, Any]:
    """Count characters in text."""
    text = params.get("text", "")
    return {
        "count": len(text),
        "count_no_spaces": len(text.replace(" ", "")),
        "text": text
    }


# ==========================================
# TOOL REGISTRY
# ==========================================

class ToolRegistry:
    """
    Registry of available tools.
    
    Simple dict wrapper. No magic.
    """
    
    DEFAULT_TOOLS = {
        "word_count": Tool(
            name="word_count",
            description="Count words in text",
            execute=tool_word_count
        ),
        "summarize": Tool(
            name="summarize",
            description="Summarize text (first sentence + stats)",
            execute=tool_summarize
        ),
        "reverse": Tool(
            name="reverse",
            description="Reverse text",
            execute=tool_reverse
        ),
        "uppercase": Tool(
            name="uppercase",
            description="Convert to uppercase",
            execute=tool_uppercase
        ),
        "lowercase": Tool(
            name="lowercase",
            description="Convert to lowercase",
            execute=tool_lowercase
        ),
        "calculate": Tool(
            name="calculate",
            description="Perform simple calculations",
            execute=tool_calculate
        ),
        "character_count": Tool(
            name="character_count",
            description="Count characters in text",
            execute=tool_character_count
        ),
    }
    
    def __init__(self):
        self._tools: Dict[str, Tool] = dict(self.DEFAULT_TOOLS)
    
    def register(self, tool: Tool) -> None:
        """Register a new tool."""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> list:
        """List all available tools."""
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
        ]
    
    def has_tool(self, name: str) -> bool:
        """Check if tool exists."""
        return name in self._tools


# ==========================================
# TOOL PROVIDER
# ==========================================

class ToolProvider(BaseProvider):
    """
    THE TOOL PROVIDER.
    
    Executes tools based on task input.
    
    Input (task.input):
        - "tool_name": Name of tool to execute
        - "parameters": Parameters for the tool
    
    Output (result.data):
        - Tool execution result
    """
    
    def __init__(self, registry: Optional[ToolRegistry] = None):
        super().__init__(
            name="tool_provider",
            capability="tool_execution",
            cost=0.0,
            latency_ms=5,
            reliability=1.0,
            priority=10
        )
        self.registry = registry or ToolRegistry()
        self.executions = 0
    
    async def execute(self, task: Task) -> ProviderResult:
        """
        Execute a tool.
        
        Task input should contain:
            - tool_name: str
            - parameters: dict
        """
        tool_name = task.input.get("tool_name")
        parameters = task.input.get("parameters", {})
        
        if not tool_name:
            return ProviderResult.fail(
                error="No tool_name provided",
                provider=self._metadata.name
            )
        
        tool = self.registry.get(tool_name)
        
        if not tool:
            return ProviderResult.fail(
                error=f"Unknown tool: {tool_name}",
                provider=self._metadata.name
            )
        
        try:
            result = tool.execute(parameters)
            self.executions += 1
            
            return ProviderResult.ok(
                data=result,
                provider=self._metadata.name
            )
        
        except Exception as e:
            return ProviderResult.fail(
                error=f"Tool execution failed: {e}",
                provider=self._metadata.name
            )


# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================

def execute_tool(tool_name: str, **params) -> Dict[str, Any]:
    """
    Synchronous tool execution.
    
    Usage:
        result = execute_tool("word_count", text="hello world")
        # result = {"count": 2, "words": ["hello", "world"]}
    """
    registry = ToolRegistry()
    tool = registry.get(tool_name)
    
    if not tool:
        return {"error": f"Unknown tool: {tool_name}"}
    
    return tool.execute(params)


# ==========================================
# EXPORTS
# ==========================================

__all__ = [
    "Tool",
    "ToolRegistry",
    "ToolProvider",
    "execute_tool",
    "tool_word_count",
    "tool_summarize",
    "tool_reverse",
    "tool_uppercase",
    "tool_lowercase",
    "tool_calculate",
]
