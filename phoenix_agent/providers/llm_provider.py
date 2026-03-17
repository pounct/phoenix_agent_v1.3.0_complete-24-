"""
Phoenix Agent v3 - LLM Provider
================================

THE REASONER.

LLMProvider provides LLM capabilities:
    - Mock mode for testing (default)
    - Real LLM integration (when configured)

SIMPLE. NO ABSTRACTION. JUST CALLS.

Author: Phoenix Agent v3.2
"""

import re
from typing import Dict, Any, Optional
from dataclasses import dataclass

import sys
sys.path.insert(0, '/home/z/my-project')

from phoenix_agent.v3.runtime.task import Task, ProviderResult
from phoenix_agent.v3.runtime.provider_contract import BaseProvider


# ==========================================
# MOCK LLM RESPONSES
# ==========================================

MOCK_RESPONSES = {
    # Definition patterns
    r"what is (.+)\?": lambda m: f"{m.group(1).strip()} is a concept or entity that can be defined in various ways depending on context.",
    
    # Explanation patterns  
    r"explain (.+)": lambda m: f"Here's an explanation of {m.group(1).strip()}: This is a complex topic that involves multiple aspects and considerations.",
    
    # Why patterns
    r"why (.+)\?": lambda m: f"There are several reasons why {m.group(1).strip()}. It depends on various factors and circumstances.",
    
    # How patterns
    r"how (do|does|can|to) (.+)\?": lambda m: f"To {m.group(2).strip()}, you would typically follow a series of steps or procedures.",
    
    # Compare patterns
    r"compare (.+)": lambda m: f"When comparing {m.group(1).strip()}, there are several similarities and differences to consider.",
    
    # Default
    "default": lambda q: f"I understand you're asking about: {q}. Let me provide a thoughtful response based on the context.",
}


# ==========================================
# LLM PROVIDER
# ==========================================

class LLMProvider(BaseProvider):
    """
    THE LLM PROVIDER.
    
    Provides LLM reasoning capabilities.
    
    Modes:
        - mock (default): Returns simulated responses
        - api: Calls real LLM API
    
    Input (task.input):
        - "prompt": The prompt to send to LLM
        - "context": Optional context
    
    Output (result.data):
        - "response": LLM response text
    """
    
    def __init__(
        self,
        mode: str = "mock",
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        api_url: Optional[str] = None
    ):
        super().__init__(
            name="llm_provider",
            capability="reasoning",
            cost=0.01,  # LLM has cost
            latency_ms=500,  # LLM is slower
            reliability=0.99,
            priority=5
        )
        self.mode = mode
        self.api_key = api_key
        self.model = model
        self.api_url = api_url
        self.calls = 0
    
    async def execute(self, task: Task) -> ProviderResult:
        """
        Execute LLM call.
        
        Supports mock mode for testing.
        """
        prompt = task.input.get("prompt", "")
        context = task.input.get("context", "")
        
        if not prompt:
            return ProviderResult.fail(
                error="No prompt provided",
                provider=self._metadata.name
            )
        
        self.calls += 1
        
        if self.mode == "mock":
            return await self._mock_execute(prompt, context)
        else:
            return await self._api_execute(prompt, context)
    
    async def _mock_execute(self, prompt: str, context: str) -> ProviderResult:
        """Mock LLM execution for testing."""
        
        # Try to match patterns
        prompt_lower = prompt.lower().strip()
        
        for pattern, handler in MOCK_RESPONSES.items():
            if pattern == "default":
                continue
            
            match = re.match(pattern, prompt_lower, re.IGNORECASE)
            if match:
                response = handler(match)
                return ProviderResult.ok(
                    data={
                        "response": response,
                        "model": "mock",
                        "mode": "mock"
                    },
                    provider=self._metadata.name
                )
        
        # Default response
        response = MOCK_RESPONSES["default"](prompt)
        
        return ProviderResult.ok(
            data={
                "response": response,
                "model": "mock",
                "mode": "mock"
            },
            provider=self._metadata.name
        )
    
    async def _api_execute(self, prompt: str, context: str) -> ProviderResult:
        """Real LLM API execution."""
        
        # Check for API configuration
        if not self.api_key:
            return ProviderResult.fail(
                error="No API key configured for real LLM calls",
                provider=self._metadata.name
            )
        
        # For now, fall back to mock if no real API
        # In production, this would call OpenAI/Anthropic/etc.
        return await self._mock_execute(prompt, context)
    
    def configure_api(self, api_key: str, model: str = "gpt-3.5-turbo", api_url: Optional[str] = None):
        """Configure for real API calls."""
        self.mode = "api"
        self.api_key = api_key
        self.model = model
        self.api_url = api_url


# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================

async def ask_llm(prompt: str, context: str = "") -> str:
    """
    Quick LLM call helper.
    
    Usage:
        response = await ask_llm("What is AI?")
    """
    provider = LLMProvider(mode="mock")
    
    task = Task(
        capability="reasoning",
        input={"prompt": prompt, "context": context}
    )
    
    result = await provider.execute(task)
    
    if result.success:
        return result.data.get("response", "")
    else:
        return f"Error: {result.error}"


# ==========================================
# EXPORTS
# ==========================================

__all__ = [
    "LLMProvider",
    "ask_llm",
    "MOCK_RESPONSES",
]