"""
LLM Client Service
统一的大语言模型调用接口，支持OpenAI和Claude
"""

import json
from typing import Optional, Any
from app.config import get_settings


class LLMClient:
    """
    Unified LLM client supporting multiple providers.
    Currently supports: OpenAI GPT-4, Anthropic Claude
    """

    def __init__(self):
        self.settings = get_settings()
        self._openai_client = None
        self._anthropic_client = None

    @property
    def openai_client(self):
        """Lazy load OpenAI client."""
        if self._openai_client is None:
            try:
                from openai import AsyncOpenAI
                self._openai_client = AsyncOpenAI(
                    api_key=self.settings.openai_api_key,
                )
            except ImportError:
                print("OpenAI package not installed")
        return self._openai_client

    @property
    def anthropic_client(self):
        """Lazy load Anthropic client."""
        if self._anthropic_client is None:
            try:
                from anthropic import AsyncAnthropic
                self._anthropic_client = AsyncAnthropic(
                    api_key=self.settings.anthropic_api_key,
                )
            except ImportError:
                print("Anthropic package not installed")
        return self._anthropic_client

    async def extract_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.1,
    ) -> dict:
        """
        Extract JSON from LLM response.

        Args:
            prompt: User prompt
            system_prompt: System instructions
            model: Model to use
            temperature: Sampling temperature

        Returns:
            Parsed JSON as dict
        """
        # Try OpenAI first
        if self.openai_client and self.settings.openai_api_key:
            return await self._openai_extract_json(
                prompt, system_prompt, model, temperature
            )

        # Fallback to Anthropic
        if self.anthropic_client and self.settings.anthropic_api_key:
            return await self._anthropic_extract_json(
                prompt, system_prompt, model, temperature
            )

        # No API key available
        return {}

    async def _openai_extract_json(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
    ) -> dict:
        """Extract JSON using OpenAI API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        return json.loads(content)

    async def _anthropic_extract_json(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
    ) -> dict:
        """Extract JSON using Anthropic API."""
        # Map model name
        claude_model = "claude-3-5-sonnet-20241022" if "4" in model else "claude-3-haiku-20240307"

        messages = [{"role": "user", "content": prompt}]

        response = await self.anthropic_client.messages.create(
            model=claude_model,
            max_tokens=4096,
            messages=messages,
            system=system_prompt,
        )

        content = response.content[0].text
        return json.loads(content)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate text using LLM.

        Args:
            prompt: User prompt
            system_prompt: System instructions
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        # Try OpenAI first
        if self.openai_client and self.settings.openai_api_key:
            return await self._openai_generate(
                prompt, system_prompt, model, temperature, max_tokens
            )

        # Fallback to Anthropic
        if self.anthropic_client and self.settings.anthropic_api_key:
            return await self._anthropic_generate(
                prompt, system_prompt, model, temperature, max_tokens
            )

        return ""


# Singleton instance
llm_client = LLMClient()


async def get_llm_response(prompt: str, **kwargs) -> dict:
    """Convenience function for LLM JSON extraction."""
    return await llm_client.extract_json(prompt, **kwargs)
