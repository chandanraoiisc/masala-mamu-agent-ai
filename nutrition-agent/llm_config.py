"""
LLM Configuration Module

This module provides a unified interface for configuring LLM providers.
It abstracts provider-specific details and provides a factory for creating
LLM instances based on a provider name.

Currently supported providers:
- OpenAI
- GitHub
- Groq
"""

import os
from typing import Dict, Optional, Any, Literal, Union
from langchain_openai import ChatOpenAI
from langchain_community.llms import GithubLLM
from langchain_groq import ChatGroq
from langchain.schema.language_model import BaseLanguageModel
from abc import ABC, abstractmethod
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMConfig(ABC):
    """Base class for LLM configurations."""

    @abstractmethod
    def create_llm(self) -> BaseLanguageModel:
        """Create and return an LLM instance."""
        pass

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate provider-specific configuration."""
        # Remove any potential API key entries
        if "api_key" in config:
            del config["api_key"]
        if "github_token" in config:
            del config["github_token"]
        if "groq_api_key" in config:
            del config["groq_api_key"]
        if "openai_api_key" in config:
            del config["openai_api_key"]

        return config


class OpenAIConfig(LLMConfig):
    """Configuration for OpenAI models."""

    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.1,
        **kwargs
    ):
        # Get API key only from environment variable
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in environment.")

        # Get model name from environment variable if not provided
        self.model_name = model_name or os.getenv("OPENAI_MODEL_NAME", "gpt-4-turbo-preview")
        self.temperature = temperature

        # Remove any API keys from kwargs
        if "api_key" in kwargs:
            del kwargs["api_key"]
        if "openai_api_key" in kwargs:
            del kwargs["openai_api_key"]

        self.kwargs = kwargs

    def create_llm(self) -> ChatOpenAI:
        """Create and return an OpenAI LLM instance."""
        return ChatOpenAI(
            api_key=self.api_key,
            model=self.model_name,
            temperature=self.temperature,
            **self.kwargs
        )


class GitHubConfig(LLMConfig):
    """Configuration for GitHub-hosted models."""

    def __init__(
        self,
        temperature: float = 0.1,
        model: str = None,
        **kwargs
    ):
        # Check if GitHub integration is available
        if GithubLLM is None:
            raise ValueError("GitHub LLM integration is not available. Install the langchain-github-llm package.")

        # Get token only from environment variable
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN in environment.")

        # Get model name with priority to parameter, then env var
        self.model = model or os.getenv("GITHUB_MODEL")
        if not self.model:
            raise ValueError("GitHub model name is required. Provide it via parameter or set GITHUB_MODEL in environment.")

        self.temperature = temperature

        # Remove any API keys from kwargs
        if "github_token" in kwargs:
            del kwargs["github_token"]

        self.kwargs = kwargs

    def create_llm(self):
        """Create and return a GitHub LLM instance."""
        if GithubLLM is None:
            raise ValueError("GitHub LLM integration is not available. Install the langchain-github-llm package.")

        return GithubLLM(
            model=self.model,
            github_token=self.github_token,
            temperature=self.temperature,
            **self.kwargs
        )


class GroqConfig(LLMConfig):
    """Configuration for Groq API models."""

    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.1,
        **kwargs
    ):
        # Get API key only from environment variable
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key is required. Set GROQ_API_KEY in environment.")

        # Get model name from environment variable if not provided
        self.model_name = model_name or os.getenv("GROQ_MODEL_NAME", "llama3-8b-8192")
        self.temperature = temperature

        # Remove any API keys from kwargs
        if "api_key" in kwargs:
            del kwargs["api_key"]
        if "groq_api_key" in kwargs:
            del kwargs["groq_api_key"]

        self.kwargs = kwargs

    def create_llm(self) -> ChatGroq:
        """Create and return a Groq LLM instance."""
        return ChatGroq(
            api_key=self.api_key,
            model=self.model_name,
            temperature=self.temperature,
            **self.kwargs
        )


def create_llm_config(
    provider: Literal["openai", "github", "groq"],
    config_params: Optional[Dict[str, Any]] = None
) -> LLMConfig:
    """
    Factory function to create an appropriate LLMConfig based on provider.

    Args:
        provider: The LLM provider ("openai", "github", or "groq")
        config_params: Provider-specific configuration parameters (NOT API keys)

    Returns:
        An instance of LLMConfig for the specified provider

    Raises:
        ValueError: If the provider is unsupported
    """
    config_params = config_params or {}

    # Sanitize any API keys that might be in the config_params
    if "api_key" in config_params:
        del config_params["api_key"]
    if "openai_api_key" in config_params:
        del config_params["openai_api_key"]
    if "github_token" in config_params:
        del config_params["github_token"]
    if "groq_api_key" in config_params:
        del config_params["groq_api_key"]

    if provider == "openai":
        return OpenAIConfig(**config_params)
    elif provider == "github":
        return GitHubConfig(**config_params)
    elif provider == "groq":
        return GroqConfig(**config_params)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_llm(
    provider: Literal["openai", "github", "groq"],
    config_params: Optional[Dict[str, Any]] = None
) -> BaseLanguageModel:
    """
    Convenience function to directly get an LLM instance.

    Args:
        provider: The LLM provider ("openai", "github", or "groq")
        config_params: Provider-specific configuration parameters (NOT API keys)

    Returns:
        An LLM instance
    """
    config = create_llm_config(provider, config_params)
    return config.create_llm()
