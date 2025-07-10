"""
Multi-provider LLM integration for RAG-YouTube.
Supports OpenAI and Google Gemini with automatic fallback and provider selection.
Adapted from PocketFlow-YT-Summarizer architecture.
"""
import os
import time
import asyncio
import logging
from typing import Optional, AsyncGenerator, Dict, Any
from abc import ABC, abstractmethod

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def __init__(self, **kwargs):
        pass
    
    @abstractmethod
    def generate(self, messages: list, **kwargs) -> str:
        """Generate a response synchronously."""
        pass
    
    @abstractmethod
    async def generate_async(self, messages: list, **kwargs) -> str:
        """Generate a response asynchronously."""
        pass
    
    @abstractmethod
    async def generate_stream(self, messages: list, **kwargs) -> AsyncGenerator[str, None]:
        """Generate a streaming response."""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate that the provider is properly configured."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, api_key: str = None, model: str = None, org_id: str = None, **kwargs):
        try:
            from openai import OpenAI, AsyncOpenAI
        except ImportError:
            raise ImportError("OpenAI package is required. Install it with: pip install openai")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.org_id = org_id or os.getenv("OPENAI_ORG_ID")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key, organization=self.org_id)
        self.async_client = AsyncOpenAI(api_key=self.api_key, organization=self.org_id)
    
    def validate_config(self) -> bool:
        """Validate OpenAI configuration."""
        return bool(self.api_key and self.api_key != "your_openai_api_key_here")
    
    def _get_model_params(self, **kwargs) -> Dict[str, Any]:
        """Get model-specific parameters."""
        model = kwargs.get('model', self.model)
        params = {
            'model': model
        }
        
        # Only add max_tokens if explicitly provided
        if 'max_tokens' in kwargs:
            params['max_tokens'] = kwargs['max_tokens']
        
        # Only add temperature if explicitly provided (except for o3 models)
        if 'temperature' in kwargs and not model.startswith("o3"):
            params['temperature'] = kwargs['temperature']
        
        return params
    
    def generate(self, messages: list, **kwargs) -> str:
        """Generate response using OpenAI."""
        params = self._get_model_params(**kwargs)
        
        try:
            response = self.client.chat.completions.create(
                messages=messages,
                **params
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
    
    async def generate_async(self, messages: list, **kwargs) -> str:
        """Generate response asynchronously using OpenAI."""
        params = self._get_model_params(**kwargs)
        
        try:
            response = await self.async_client.chat.completions.create(
                messages=messages,
                **params
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI async generation failed: {e}")
            raise
    
    async def generate_stream(self, messages: list, **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming response using OpenAI."""
        params = self._get_model_params(**kwargs)
        
        try:
            stream = await self.async_client.chat.completions.create(
                messages=messages,
                stream=True,
                **params
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise


class GeminiProvider(LLMProvider):
    """Google Gemini provider implementation."""
    
    def __init__(self, api_key: str = None, model: str = None, **kwargs):
        try:
            import google.generativeai as genai
            self.genai = genai
        except ImportError:
            raise ImportError("Google Generative AI package is required. Install it with: pip install google-generativeai")
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        self.genai.configure(api_key=self.api_key)
        
        # Safety settings to be less restrictive
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ]
    
    def validate_config(self) -> bool:
        """Validate Gemini configuration."""
        return bool(self.api_key and self.api_key != "your_gemini_api_key_here")
    
    def _messages_to_prompt(self, messages: list) -> str:
        """Convert OpenAI-style messages to a single prompt for Gemini."""
        prompt_parts = []
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"Instructions: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def _create_model(self, **kwargs):
        """Create a Gemini model instance."""
        return self.genai.GenerativeModel(self.model_name)
    
    def _get_generation_config(self, **kwargs):
        """Get generation configuration for Gemini."""
        config = {}
        
        # Only set max_output_tokens if explicitly provided
        # Due to known issues with Gemini 2.5 Pro, avoid setting this by default
        if 'max_tokens' in kwargs:
            # Cap at 8192 (standard Gemini API limit) for safety
            max_tokens = min(kwargs['max_tokens'], 8192)
            config['max_output_tokens'] = max_tokens
        
        # Only add temperature if explicitly provided
        if 'temperature' in kwargs:
            config['temperature'] = kwargs['temperature']
        
        return self.genai.types.GenerationConfig(**config)
    
    def generate(self, messages: list, **kwargs) -> str:
        """Generate response using Gemini."""
        prompt = self._messages_to_prompt(messages)
        model = self._create_model()
        generation_config = self._get_generation_config(**kwargs)
        
        try:
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )
            
            # Handle response validation
            if not response.candidates or len(response.candidates) == 0:
                raise Exception("No candidates returned from Gemini API")
            
            candidate = response.candidates[0]
            
            # Check for safety blocks or other issues
            if hasattr(candidate, 'finish_reason') and candidate.finish_reason != 1:
                if candidate.finish_reason == 3:  # SAFETY
                    raise Exception("Content was blocked by safety filters")
                elif candidate.finish_reason == 2:  # MAX_TOKENS
                    # For max tokens, just return what we got
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        return candidate.content.parts[0].text
            
            # Extract text response
            if candidate.content.parts:
                return candidate.content.parts[0].text
            else:
                raise Exception("No valid response text returned from Gemini API")
                
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise
    
    async def generate_async(self, messages: list, **kwargs) -> str:
        """Generate response asynchronously using Gemini."""
        # Gemini doesn't have native async support, so we'll run in thread
        import asyncio
        return await asyncio.to_thread(self.generate, messages, **kwargs)
    
    async def generate_stream(self, messages: list, **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming response using Gemini."""
        # Gemini doesn't have native streaming, so we'll simulate it
        response = await self.generate_async(messages, **kwargs)
        
        # Split response into chunks for streaming effect
        words = response.split()
        chunk_size = max(1, len(words) // 20)  # ~20 chunks
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            if i + chunk_size < len(words):
                chunk += ' '
            yield chunk
            await asyncio.sleep(0.05)  # Small delay for streaming effect


class LLMManager:
    """Manager class for handling multiple LLM providers."""
    
    def __init__(self, config=None):
        self.config = config
        self.providers = {}
        self._setup_providers()
    
    def _setup_providers(self):
        """Initialize available providers."""
        # Setup OpenAI if configured
        try:
            if os.getenv("OPENAI_API_KEY"):
                openai_config = {}
                if self.config:
                    openai_config = {
                        'api_key': self.config.openai_api_key(),
                        'model': self.config.openai_model(),
                        'org_id': self.config.openai_org_id()
                    }
                
                self.providers['openai'] = OpenAIProvider(**openai_config)
                logger.info("OpenAI provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI provider: {e}")
        
        # Setup Gemini if configured
        try:
            if os.getenv("GEMINI_API_KEY"):
                gemini_config = {
                    'api_key': os.getenv("GEMINI_API_KEY"),
                    'model': os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
                }
                
                self.providers['gemini'] = GeminiProvider(**gemini_config)
                logger.info("Gemini provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini provider: {e}")
    
    def get_provider(self, provider_name: str = None) -> LLMProvider:
        """Get a specific provider or the default one."""
        if provider_name:
            if provider_name not in self.providers:
                raise ValueError(f"Provider '{provider_name}' not available. Available: {list(self.providers.keys())}")
            return self.providers[provider_name]
        
        # Get default provider
        default_provider = os.getenv("LLM_PROVIDER", "openai").lower()
        if default_provider in self.providers:
            return self.providers[default_provider]
        
        # Fallback to any available provider
        if self.providers:
            provider_name = list(self.providers.keys())[0]
            logger.warning(f"Default provider '{default_provider}' not available, using '{provider_name}'")
            return self.providers[provider_name]
        
        raise ValueError("No LLM providers are available. Please check your API keys.")
    
    def list_providers(self) -> list:
        """List available providers."""
        return list(self.providers.keys())
    
    def test_provider(self, provider_name: str) -> bool:
        """Test if a provider is working."""
        if provider_name not in self.providers:
            return False
        
        try:
            provider = self.providers[provider_name]
            test_messages = [{"role": "user", "content": "Hello, respond with 'success' to test the connection."}]
            response = provider.generate(test_messages, max_tokens=10)
            logger.info(f"✅ {provider_name.upper()} test successful: {response[:50]}...")
            return True
        except Exception as e:
            logger.error(f"❌ {provider_name.upper()} test failed: {e}")
            return False
    
    def test_all_providers(self) -> Dict[str, bool]:
        """Test all available providers."""
        results = {}
        for provider_name in self.providers:
            results[provider_name] = self.test_provider(provider_name)
        return results