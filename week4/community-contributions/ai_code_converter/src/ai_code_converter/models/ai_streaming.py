"""Module for handling AI model streaming responses."""

import logging
import time
from typing import Generator, Any, Callable, TypeVar, cast
from anthropic import Anthropic, AnthropicError, APIError, RateLimitError, AuthenticationError
import google.generativeai as genai
from openai import OpenAI

from src.ai_code_converter.config import (
    OPENAI_MODEL,
    CLAUDE_MODEL,
    DEEPSEEK_MODEL,
    GEMINI_MODEL,
    GROQ_MODEL
)

logger = logging.getLogger(__name__)

# Type variable for generic retry function
T = TypeVar('T')

def retry_with_exponential_backoff(
    max_retries: int = 5,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,),
    retryable_return: Callable[[Any], bool] = None,
) -> Callable:
    """Retry decorator with exponential backoff
    
    Args:
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Add random jitter to delay
        retryable_exceptions: Exceptions that trigger retry
        retryable_return: Function that takes the return value and returns
            True if it should be retried
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Initialize variables
            num_retries = 0
            delay = initial_delay
            
            # Loop until max retries reached
            while True:
                try:
                    response = func(*args, **kwargs)
                    
                    # Check if we should retry based on response value
                    if retryable_return and num_retries < max_retries:
                        try:
                            if retryable_return(response):
                                num_retries += 1
                                logger.warning(
                                    f"Retrying {func.__name__} due to response condition "
                                    f"(attempt {num_retries} of {max_retries})"
                                )
                                time.sleep(delay)
                                delay = calculate_next_delay(delay, exponential_base, jitter)
                                continue
                        except Exception as e:
                            # If retryable_return itself fails, log and continue
                            logger.warning(f"Error in retry condition: {e}")
                    
                    return response
                    
                except retryable_exceptions as e:
                    # Check if we've exceeded max retries
                    if num_retries >= max_retries:
                        logger.error(
                            f"Maximum retries ({max_retries}) exceeded for {func.__name__}: {str(e)}"
                        )
                        raise
                    
                    # Handle specific error types with custom messages
                    if hasattr(e, 'error') and isinstance(e.error, dict) and e.error.get('type') == 'overloaded_error':
                        logger.warning(
                            f"Service overloaded, retrying {func.__name__} "
                            f"(attempt {num_retries + 1} of {max_retries})"
                        )
                    else:
                        logger.warning(
                            f"Exception in {func.__name__}, retrying "
                            f"(attempt {num_retries + 1} of {max_retries}): {str(e)}"
                        )
                    
                    # Increment retry count and delay
                    num_retries += 1
                    time.sleep(delay)
                    delay = calculate_next_delay(delay, exponential_base, jitter)
        
        return cast(Callable, wrapper)
    return decorator


def calculate_next_delay(current_delay: float, exponential_base: float, jitter: bool) -> float:
    """Calculate the next delay time using exponential backoff and optional jitter"""
    import random
    delay = current_delay * exponential_base
    # Add jitter - random value between -0.2 and +0.2 of the delay
    if jitter:
        delay = delay * (1 + random.uniform(-0.2, 0.2))
    return delay


class AIModelStreamer:
    """Class for handling streaming responses from various AI models."""
    
    def __init__(self, openai_client: OpenAI, claude_client: Anthropic,
                 deepseek_client: OpenAI, groq_client: OpenAI, gemini_model: genai.GenerativeModel):
        """Initialize with AI model clients."""
        self.openai = openai_client
        self.claude = claude_client
        self.deepseek = deepseek_client
        self.groq = groq_client
        self.gemini = gemini_model
        self.max_retries = 5

    @retry_with_exponential_backoff(
        max_retries=5, 
        initial_delay=1.0, 
        retryable_exceptions=(Exception,)
    )
    def _call_gpt_api(self, prompt: str):
        """Call the GPT API with retry logic"""
        messages = [{"role": "user", "content": prompt}]
        return self.openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            stream=True
        )

    def stream_gpt(self, prompt: str) -> Generator[str, None, None]:
        """Stream responses from GPT model."""
        try:
            stream = self._call_gpt_api(prompt)
            
            response = ""
            for chunk in stream:
                fragment = chunk.choices[0].delta.content or ""
                response += fragment
                yield response
                
        except Exception as e:
            logger.error(f"GPT API error: {str(e)}", exc_info=True)
            yield f"Error with GPT API: {str(e)}"

    @retry_with_exponential_backoff(
        max_retries=5, 
        initial_delay=1.0, 
        exponential_base=2.0,
        retryable_exceptions=(Exception,)
    )
    def _call_claude_api(self, prompt: str):
        """Call the Claude API with retry logic"""
        return self.claude.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
    
    def stream_claude(self, prompt: str) -> Generator[str, None, None]:
        """Stream responses from Claude model with retry for overloaded errors."""
        retry_count = 0
        max_retries = self.max_retries
        delay = 1.0
        
        while True:
            try:
                result = self._call_claude_api(prompt)
                
                response = ""
                with result as stream:
                    for text in stream.text_stream:
                        response += text
                        yield response
                
                # If we get here, we succeeded, so break out of retry loop
                break
                    
            except (AnthropicError, APIError) as e:
                # Special handling for overloaded_error
                if hasattr(e, 'error') and getattr(e, 'error', {}).get('type') == 'overloaded_error':
                    if retry_count < max_retries:
                        retry_count += 1
                        wait_time = delay * (2 ** (retry_count - 1))  # Exponential backoff
                        logger.warning(f"Claude API overloaded, retrying in {wait_time:.2f}s (attempt {retry_count}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                
                # If reached maximum retries or not an overloaded error
                logger.error(f"Claude API error: {str(e)}", exc_info=True)
                yield f"Error with Claude API: {str(e)}"
                break
                
            except Exception as e:
                logger.error(f"Claude API error: {str(e)}", exc_info=True)
                yield f"Error with Claude API: {str(e)}"
                break

    @retry_with_exponential_backoff(
        max_retries=5, 
        initial_delay=1.0, 
        retryable_exceptions=(Exception,)
    )
    def _call_deepseek_api(self, prompt: str):
        """Call the DeepSeek API with retry logic"""
        messages = [{"role": "user", "content": prompt}]
        return self.deepseek.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=4000
        )

    def stream_deepseek(self, prompt: str) -> Generator[str, None, None]:
        """Stream responses from DeepSeek model."""
        try:
            stream = self._call_deepseek_api(prompt)
            
            reply = ""
            for chunk in stream:
                fragment = chunk.choices[0].delta.content or ""
                reply += fragment
                yield reply
                
        except Exception as e:
            logger.error(f"DeepSeek API error: {str(e)}", exc_info=True)
            yield f"Error with DeepSeek API: {str(e)}"

    @retry_with_exponential_backoff(
        max_retries=5, 
        initial_delay=1.0, 
        retryable_exceptions=(Exception,)
    )
    def _call_groq_api(self, prompt: str):
        """Call the GROQ API with retry logic"""
        messages = [{"role": "user", "content": prompt}]
        return self.groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=4000
        )

    def stream_groq(self, prompt: str) -> Generator[str, None, None]:
        """Stream responses from GROQ model."""
        try:
            stream = self._call_groq_api(prompt)
            
            reply = ""
            for chunk in stream:
                fragment = chunk.choices[0].delta.content or ""
                reply += fragment
                yield reply
                
        except Exception as e:
            logger.error(f"GROQ API error: {str(e)}", exc_info=True)
            yield f"Error with GROQ API: {str(e)}"

    @retry_with_exponential_backoff(
        max_retries=5, 
        initial_delay=1.0, 
        retryable_exceptions=(Exception,)
    )
    def _call_gemini_api(self, prompt: str):
        """Call the Gemini API with retry logic"""
        return self.gemini.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 4000,
            },
            stream=True
        )

    def stream_gemini(self, prompt: str) -> Generator[str, None, None]:
        """Stream responses from Gemini model."""
        try:
            response = self._call_gemini_api(prompt)
            
            reply = ""
            for chunk in response:
                if chunk.text:
                    reply += chunk.text
                    yield reply
                    
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}", exc_info=True)
            yield f"Error with Gemini API: {str(e)}" 