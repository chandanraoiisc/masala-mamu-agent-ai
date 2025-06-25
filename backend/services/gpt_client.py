import json
import logging
from typing import Dict, Any, List, Optional
import openai
from openai import AzureOpenAI
from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPTClient:
    """Client for interacting with Azure OpenAI API"""

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None,
                 api_version: Optional[str] = None, deployment: Optional[str] = None):
        """Initialize the Azure OpenAI client"""
        self.api_key = api_key or settings.AZURE_OPENAI_API_KEY
        self.endpoint = endpoint or settings.AZURE_OPENAI_ENDPOINT
        self.api_version = api_version or settings.AZURE_OPENAI_API_VERSION
        self.deployment = deployment or settings.AZURE_OPENAI_DEPLOYMENT

        if not self.api_key:
            logger.warning("No Azure OpenAI API key provided!")
        if not self.endpoint:
            logger.warning("No Azure OpenAI endpoint provided!")
        if not self.deployment:
            logger.warning("No Azure OpenAI deployment name provided!")

        logger.info(f"Initializing Azure OpenAI client with deployment: {self.deployment}")

        try:
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint
            )
            logger.info("Azure OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
            raise

    async def generate_completion(self,
                                  prompt: str,
                                  system_message: str = "You are a helpful assistant.",
                                  temperature: float = None) -> str:
        """
        Generate a completion using the Azure OpenAI API

        Args:
            prompt: The user prompt
            system_message: The system message to set context
            temperature: Temperature for response generation (0.0 to 1.0)

        Returns:
            The generated text response
        """
        temperature = temperature if temperature is not None else settings.OPENAI_TEMPERATURE

        try:
            logger.info(f"Sending completion request to Azure OpenAI API with prompt: {prompt[:50]}...")
            response = self.client.chat.completions.create(
                model=self.deployment,  # For Azure, model is the deployment name
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature
            )
            logger.info("Received response from Azure OpenAI API")
            return response.choices[0].message.content

        except openai.APIError as e:
            logger.error(f"Azure OpenAI API Error: {str(e)}")
            raise ConnectionError(f"Azure OpenAI API Error: {str(e)}")
        except openai.APIConnectionError as e:
            logger.error(f"Failed to connect to Azure OpenAI API: {str(e)}")
            raise ConnectionError(f"Failed to connect to Azure OpenAI API: {str(e)}")
        except openai.RateLimitError as e:
            logger.error(f"Azure OpenAI API rate limit exceeded: {str(e)}")
            raise ConnectionError(f"Azure OpenAI API rate limit exceeded: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in generate_completion: {str(e)}")
            raise ConnectionError(f"Unexpected error: {str(e)}")

    async def generate_structured_output(self,
                                         prompt: str,
                                         system_message: str,
                                         output_schema: Dict[str, Any],
                                         temperature: float = None) -> Dict[str, Any]:
        """
        Generate a structured JSON output using the Azure OpenAI API

        Args:
            prompt: The user prompt
            system_message: The system message to set context
            output_schema: JSON schema for the expected output
            temperature: Temperature for response generation (0.0 to 1.0)

        Returns:
            Structured data according to the provided schema
        """
        temperature = temperature if temperature is not None else settings.OPENAI_TEMPERATURE

        # Add schema instructions to the system message
        schema_instructions = f"\nYou must respond with a JSON object that conforms to this schema: {json.dumps(output_schema)}"
        full_system_message = system_message + schema_instructions

        try:
            logger.info(f"Sending structured output request to Azure OpenAI API with prompt: {prompt[:50]}...")
            response = self.client.chat.completions.create(
                model=self.deployment,  # For Azure, model is the deployment name
                messages=[
                    {"role": "system", "content": full_system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            logger.info("Received response from Azure OpenAI API")

            # Parse the JSON response
            try:
                return json.loads(response.choices[0].message.content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.error(f"Raw response: {response.choices[0].message.content}")
                raise ValueError(f"Failed to parse JSON response: {str(e)}")

        except openai.APIError as e:
            logger.error(f"Azure OpenAI API Error: {str(e)}")
            raise ConnectionError(f"Azure OpenAI API Error: {str(e)}")
        except openai.APIConnectionError as e:
            logger.error(f"Failed to connect to Azure OpenAI API: {str(e)}")
            raise ConnectionError(f"Failed to connect to Azure OpenAI API: {str(e)}")
        except openai.RateLimitError as e:
            logger.error(f"Azure OpenAI API rate limit exceeded: {str(e)}")
            raise ConnectionError(f"Azure OpenAI API rate limit exceeded: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in generate_structured_output: {str(e)}")
            raise ConnectionError(f"Unexpected error: {str(e)}")
