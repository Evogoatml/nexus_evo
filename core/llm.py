"""
LLM interface for nexus_evo using OpenAI
"""
import openai
from typing import List, Dict, Optional, Generator
from app_config import config
from utils import get_logger, LLMError, retry


logger = get_logger(__name__, config.log_file, config.log_level)


class LLMInterface:
    """OpenAI LLM interface with streaming support"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.llm.api_key)
        self.model = config.llm.model
        self.temperature = config.llm.temperature
        self.max_tokens = config.llm.max_tokens
        logger.info(f"LLM initialized with model: {self.model}")
    
    @retry(max_attempts=3, delay=1.0)
    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str | Generator[str, None, None]:
        """
        Generate completion from messages
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens
            stream: Enable streaming response
            
        Returns:
            Complete response string or generator for streaming
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=stream
            )
            
            if stream:
                return self._stream_response(response)
            else:
                content = response.choices[0].message.content
                logger.debug(f"LLM response length: {len(content)} chars")
                return content
                
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMError(f"API error: {e}")
        except openai.APIConnectionError as e:
            logger.error(f"OpenAI connection error: {e}")
            raise LLMError(f"Connection error: {e}")
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit: {e}")
            raise LLMError(f"Rate limit: {e}")
        except Exception as e:
            logger.error(f"Unexpected LLM error: {e}")
            raise LLMError(f"Unexpected error: {e}")
    
    def generate_from_prompt(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False
    ) -> str | Generator[str, None, None]:
        """
        Generate completion from a simple prompt string
        
        Args:
            prompt: Text prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            stream: Enable streaming response
            
        Returns:
            Complete response string or generator for streaming
        """
        messages = [{"role": "user", "content": prompt}]
        return self.generate(messages, temperature, max_tokens, stream)

    def _stream_response(self, response) -> Generator[str, None, None]:
        """Stream response chunks"""
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate text embedding using OpenAI
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=config.memory.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            raise LLMError(f"Embedding error: {e}")
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation)
        OpenAI tiktoken would be more accurate but this is lightweight
        """
        return len(text) // 4
    
    def format_messages(
        self,
        system_prompt: str,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """
        Format messages for LLM
        
        Args:
            system_prompt: System instruction
            user_message: Current user message
            history: Previous conversation history
            
        Returns:
            Formatted message list
        """
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": user_message})
        
        return messages




