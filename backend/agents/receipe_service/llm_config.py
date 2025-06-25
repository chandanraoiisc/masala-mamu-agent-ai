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
from langchain_groq import ChatGroq
from langchain.schema.language_model import BaseLanguageModel
from abc import ABC, abstractmethod
from dotenv import load_dotenv

# Setup logger

# Load environment variables
load_dotenv(dotenv_path=os.path.join("agents/health_diet_agent", ".env"))


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
        for key in ["api_key", "github_token", "groq_api_key", "openai_api_key"]:
            if key in config:
                del config[key]

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
        for key in ["api_key", "openai_api_key"]:
            if key in kwargs:
                del kwargs[key]

        self.kwargs = kwargs

    def create_llm(self) -> ChatOpenAI:
        """Create and return an OpenAI LLM instance."""
        try:
            llm = ChatOpenAI(
                api_key=self.api_key,
                model=self.model_name,
                temperature=self.temperature,
                **self.kwargs
            )
            return llm
        except Exception as e:
            raise


class GitHubConfig(LLMConfig):
    """Configuration for GitHub-hosted models."""

    def __init__(
        self,
        temperature: float = 0.1,
        model: str = None,
        top_p: float = 1.0,
        **kwargs
    ):
        # Get token only from environment variable
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN in environment.")

        # Get model name with priority to parameter, then env var
        self.model = model or os.getenv("GITHUB_MODEL")
        if not self.model:
            raise ValueError("GitHub model name is required. Provide it via parameter or set GITHUB_MODEL in environment.")

        self.temperature = temperature
        self.top_p = top_p
        self.endpoint = "https://models.github.ai/inference"
        # logger.info(f"Using GitHub model: {self.model} with temperature: {self.temperature}, top_p: {self.top_p}")
        # logger.debug(f"Using GitHub API endpoint: {self.endpoint}")

        # Remove any API keys from kwargs
        if "github_token" in kwargs:
            # logger.warning("Removing github_token from kwargs")
            del kwargs["github_token"]

        self.kwargs = kwargs
        # logger.debug(f"Additional GitHub parameters: {list(self.kwargs.keys())}")

    def create_llm(self) -> ChatOpenAI:
        """Create and return a GitHub LLM instance using ChatOpenAI."""
        # logger.info(f"Creating GitHub LLM instance with model: {self.model}")
        try:
            llm = ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                top_p=self.top_p,
                base_url=self.endpoint,
                api_key=self.github_token,
                **self.kwargs
            )
            # logger.info("GitHub LLM instance created successfully")
            return llm
        except Exception as e:
            # logger.error(f"Error creating GitHub LLM: {str(e)}")
            raise


class GroqConfig(LLMConfig):
    """Configuration for Groq API models."""

    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.1,
        **kwargs
    ):
        # logger.info("Initializing Groq LLM configuration")
        # Get API key only from environment variable
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            # logger.error("Groq API key not found in environment")
            raise ValueError("Groq API key is required. Set GROQ_API_KEY in environment.")

        # Get model name from environment variable if not provided
        self.model_name = model_name or os.getenv("GROQ_MODEL_NAME", "llama3-8b-8192")
        self.temperature = temperature
        # logger.info(f"Using Groq model: {self.model_name} with temperature: {self.temperature}")

        # Remove any API keys from kwargs
        for key in ["api_key", "groq_api_key"]:
            if key in kwargs:
                # logger.warning(f"Removing sensitive key '{key}' from kwargs")
                del kwargs[key]

        self.kwargs = kwargs
        # logger.debug(f"Additional Groq parameters: {list(self.kwargs.keys())}")

    def create_llm(self) -> ChatGroq:
        """Create and return a Groq LLM instance."""
        # logger.info(f"Creating Groq ChatLLM instance with model: {self.model_name}")
        try:
            llm = ChatGroq(
                api_key=self.api_key,
                model=self.model_name,
                temperature=self.temperature,
                **self.kwargs
            )
            # logger.info("Groq LLM instance created successfully")
            return llm
        except Exception as e:
            # logger.error(f"Error creating Groq LLM: {str(e)}")
            raise


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
    # logger.info(f"Creating LLM config for provider: {provider}")
    config_params = config_params or {}
    # logger.debug(f"Configuration parameters received: {list(config_params.keys())}")

    # Sanitize any API keys that might be in the config_params
    sensitive_keys = ["api_key", "openai_api_key", "github_token", "groq_api_key"]
    for key in sensitive_keys:
        if key in config_params:
            # logger.warning(f"Removing sensitive key '{key}' from config parameters")
            del config_params[key]

    try:
        if provider == "openai":
            # logger.info("Creating OpenAI configuration")
            return OpenAIConfig(**config_params)
        elif provider == "github":
            # logger.info("Creating GitHub configuration")
            return GitHubConfig(**config_params)
        elif provider == "groq":
            # logger.info("Creating Groq configuration")
            return GroqConfig(**config_params)
        else:
            # logger.error(f"Unsupported LLM provider: {provider}")
            raise ValueError(f"Unsupported LLM provider: {provider}")
    except Exception as e:
        # logger.error(f"Error creating LLM config for {provider}: {str(e)}")
        raise


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
    # logger.info(f"Getting LLM instance for provider: {provider}")
    try:
        config = create_llm_config(provider, config_params)
        llm = config.create_llm()
        # logger.info(f"Successfully created {provider} LLM instance")
        return llm
    except Exception as e:
        # logger.error(f"Failed to create LLM for {provider}: {str(e)}")
        raise
