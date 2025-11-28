#!/usr/bin/env python3
"""
Gemini API Client for RKL Secure Reasoning Brief
Supports hybrid model approach: Gemini for critical QA, Llama for bulk processing

This module demonstrates the use of Google's Gemini API as learned in the
5-Day AI Agents Intensive Course, while maintaining RKL's zero-cost local
processing philosophy through intelligent fallback mechanisms.
"""

import os
import sys
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Import RKL logging for research telemetry
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from rkl_logging import sha256_text
    RKL_LOGGING_AVAILABLE = True
except ImportError:
    RKL_LOGGING_AVAILABLE = False

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

if not RKL_LOGGING_AVAILABLE:
    logger.warning("rkl_logging not available - Gemini telemetry disabled")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Gemini features will be unavailable.")

# Import Vertex AI SDK if enabled
USE_VERTEX_AI = os.getenv('USE_VERTEX_AI', 'false').lower() == 'true'
if USE_VERTEX_AI:
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        VERTEX_AI_AVAILABLE = True
        logger.info("Vertex AI SDK loaded - using paid tier")
    except ImportError:
        VERTEX_AI_AVAILABLE = False
        logger.error("USE_VERTEX_AI=true but google-cloud-aiplatform not installed")
        USE_VERTEX_AI = False
else:
    VERTEX_AI_AVAILABLE = False


class GeminiClient:
    """
    Client for interacting with Google's Gemini API.

    This client provides a unified interface for Gemini API calls with:
    - Automatic API key configuration
    - Error handling and fallback support
    - Token usage tracking
    - Integration with RKL's audit framework

    Attributes:
        model_name (str): Gemini model to use (e.g., 'gemini-2.0-flash')
        api_key (str): Google AI Studio API key
        model: Configured Gemini model instance
    """

    def __init__(self, model_name: str = "gemini-2.0-flash", api_key: Optional[str] = None,
                 research_logger: Optional['StructuredLogger'] = None):
        """
        Initialize Gemini client (AI Studio or Vertex AI).

        Args:
            model_name: Name of Gemini model to use
            api_key: Optional API key (defaults to GOOGLE_API_KEY env var, ignored if Vertex AI)
            research_logger: Optional StructuredLogger for research telemetry

        Raises:
            ImportError: If required SDK not installed
            ValueError: If credentials not configured
        """
        self.model_name = model_name
        self.research_logger = research_logger
        self.use_vertex_ai = USE_VERTEX_AI

        # Rate limiting (only for free tier AI Studio)
        self.last_request_time = 0
        self.min_request_interval = 0 if USE_VERTEX_AI else 4.5  # No limit for Vertex AI paid tier

        if USE_VERTEX_AI and VERTEX_AI_AVAILABLE:
            # Vertex AI paid tier setup
            project_id = os.getenv('VERTEX_AI_PROJECT_ID')
            location = os.getenv('VERTEX_AI_LOCATION', 'us-central1')
            credentials_path = os.getenv('VERTEX_AI_CREDENTIALS')

            if not project_id:
                raise ValueError("VERTEX_AI_PROJECT_ID not set in environment")
            if not credentials_path or not Path(credentials_path).exists():
                raise ValueError(f"VERTEX_AI_CREDENTIALS not found: {credentials_path}")

            # Set credentials environment variable for Vertex AI
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

            # Initialize Vertex AI
            vertexai.init(project=project_id, location=location)
            self.model = GenerativeModel(self.model_name)

            logger.info(f"✅ Initialized Vertex AI client (PAID TIER - NO RATE LIMITING)")
            logger.info(f"   Project: {project_id}, Location: {location}, Model: {self.model_name}")

        else:
            # AI Studio free tier setup
            if not GEMINI_AVAILABLE:
                raise ImportError(
                    "google-generativeai package required. "
                    "Install with: pip install google-generativeai"
                )

            self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
            if not self.api_key:
                raise ValueError(
                    "GOOGLE_API_KEY not found. Set in environment or .env file. "
                    "Get key from: https://aistudio.google.com/app/apikey"
                )

            # Configure AI Studio
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)

            logger.info(f"Initialized AI Studio client (FREE TIER - Rate limited)")
            logger.info(f"Rate limiting: {self.min_request_interval}s between requests")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        agent_id: str = "gemini_qa",
        session_id: Optional[str] = None,
        turn_id: Optional[int] = None,
        task_type: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text using Gemini API with research telemetry.

        Args:
            prompt: User prompt to send to model
            system_prompt: Optional system instructions (prepended to prompt)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            agent_id: Agent identifier for telemetry
            session_id: Session identifier for telemetry
            turn_id: Turn number for telemetry
            task_type: Task type (e.g., 'qa_review', 'fact_check')
            **kwargs: Additional generation parameters

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails (should be caught by caller for fallback)
        """
        start_time = time.time()

        # Log boundary event: external API call (Type III)
        if self.research_logger and RKL_LOGGING_AVAILABLE:
            self.research_logger.log("boundary_event", {
                "event_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "t": int(time.time() * 1000),
                "session_id": session_id or "unknown",
                "agent_id": agent_id,
                "rule_id": "type3.external_api.gemini",
                "trigger_tag": task_type or "qa_review",
                "context_tag": "external_qa",
                "action": "allow"
            })

        try:
            # Rate limiting: only for free tier AI Studio
            if self.min_request_interval > 0:
                time_since_last_request = time.time() - self.last_request_time
                if time_since_last_request < self.min_request_interval:
                    sleep_time = self.min_request_interval - time_since_last_request
                    logger.info(f"Rate limiting: sleeping {sleep_time:.2f}s before API call")
                    time.sleep(sleep_time)

            # Combine system prompt and user prompt if both provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Configure generation parameters
            if self.use_vertex_ai:
                # Vertex AI uses different config format
                from vertexai.generative_models import GenerationConfig
                generation_config = GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens if max_tokens else 8192
                )
            else:
                # AI Studio config
                generation_config = genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    **kwargs
                )

            # Generate response
            api_type = "Vertex AI" if self.use_vertex_ai else "AI Studio"
            logger.debug(f"Calling {api_type} with prompt length: {len(full_prompt)} chars")
            self.last_request_time = time.time()  # Update timestamp before call
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )

            # Extract text from response
            if not response or not response.text:
                logger.warning(f"{api_type} returned empty response")
                return ""

            # Calculate metrics
            latency_ms = int((time.time() - start_time) * 1000)

            # Try to get token counts from usage_metadata
            prompt_tokens = None
            gen_tokens = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                prompt_tokens = getattr(response.usage_metadata, 'prompt_token_count', None)
                gen_tokens = getattr(response.usage_metadata, 'candidates_token_count', None)

            # Log execution context for research
            if self.research_logger and RKL_LOGGING_AVAILABLE:
                self.research_logger.log("execution_context", {
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "session_id": session_id or "unknown",
                    "turn_id": turn_id or 0,
                    "agent_id": agent_id,
                    "model_id": self.model_name,
                    "model_rev": "api",
                    "temp": temperature,
                    "top_p": None,
                    "ctx_tokens_used": prompt_tokens if prompt_tokens else len(full_prompt.split()),
                    "gen_tokens": gen_tokens if gen_tokens else len(response.text.split()),
                    "tool_lat_ms": latency_ms,
                    "prompt_id_hash": sha256_text(prompt) if RKL_LOGGING_AVAILABLE else "",
                    "system_prompt_hash": sha256_text(system_prompt) if system_prompt and RKL_LOGGING_AVAILABLE else "",
                    "token_estimation": "api" if prompt_tokens else "word_count"
                })

            logger.info(f"Gemini generated {len(response.text)} chars in {latency_ms}ms")
            return response.text

        except Exception as e:
            logger.error(f"Gemini API error: {e}")

            # Log boundary event: failure
            if self.research_logger and RKL_LOGGING_AVAILABLE:
                self.research_logger.log("boundary_event", {
                    "event_id": str(uuid.uuid4()),
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "t": int(time.time() * 1000),
                    "session_id": session_id or "unknown",
                    "agent_id": agent_id,
                    "rule_id": "type3.external_api.gemini",
                    "trigger_tag": "api_error",
                    "context_tag": "external_qa_failure",
                    "action": "block"
                })

            raise  # Re-raise to allow caller to handle fallback

    def check_availability(self) -> bool:
        """
        Test if Gemini API is available and working.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            test_response = self.generate("Respond with 'OK' if you can read this.")
            return bool(test_response)
        except Exception as e:
            logger.error(f"Gemini availability check failed: {e}")
            return False


class HybridModelClient:
    """
    Hybrid client that uses Gemini for critical tasks with Ollama fallback.

    This implements RKL's intelligent model selection strategy:
    - Gemini: For critical QA, fact-checking, governance tasks
    - Ollama (local): For bulk processing, summarization, metadata extraction

    Provides automatic fallback if Gemini is unavailable or rate-limited.

    Attributes:
        gemini_client: GeminiClient instance (or None if unavailable)
        ollama_client: OllamaClient instance for fallback
        use_gemini_for: List of task types to prefer Gemini
    """

    def __init__(
        self,
        ollama_client,
        gemini_model: str = "gemini-2.0-flash",
        use_gemini_for: Optional[list] = None,
        research_logger: Optional['StructuredLogger'] = None
    ):
        """
        Initialize hybrid client with both Gemini and Ollama.

        Args:
            ollama_client: Configured OllamaClient instance
            gemini_model: Gemini model name to use
            use_gemini_for: List of task types to prefer Gemini for
                           (e.g., ['qa_review', 'fact_check', 'governance'])
            research_logger: Optional StructuredLogger for research telemetry
        """
        self.ollama_client = ollama_client
        self.research_logger = research_logger

        # Try to initialize Gemini (may fail if not available)
        try:
            self.gemini_client = GeminiClient(model_name=gemini_model, research_logger=research_logger)
            self.gemini_available = self.gemini_client.check_availability()
            logger.info("Gemini client initialized and available")
        except Exception as e:
            logger.warning(f"Gemini initialization failed: {e}. Using Ollama only.")
            self.gemini_client = None
            self.gemini_available = False

        # Default task types for Gemini (critical tasks)
        self.use_gemini_for = use_gemini_for or [
            'qa_review',
            'fact_check',
            'governance',
            'compliance_check'
        ]

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        task_type: Optional[str] = None,
        prefer_gemini: bool = False,
        agent_id: str = "hybrid_qa",
        session_id: Optional[str] = None,
        turn_id: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using appropriate model based on task type with telemetry.

        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            task_type: Type of task (determines model selection)
            prefer_gemini: Force Gemini if available
            agent_id: Agent identifier for telemetry
            session_id: Session identifier for telemetry
            turn_id: Turn number for telemetry
            **kwargs: Additional generation parameters

        Returns:
            Dict with keys:
                - response: Generated text
                - model_used: 'gemini' or 'ollama'
                - success: bool
        """
        # Determine which model to use
        should_use_gemini = (
            self.gemini_available and (
                prefer_gemini or
                task_type in self.use_gemini_for
            )
        )

        # Log reasoning graph edge: route decision
        if self.research_logger and RKL_LOGGING_AVAILABLE:
            self.research_logger.log("reasoning_graph_edge", {
                "session_id": session_id or "unknown",
                "edge_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "t": int(time.time() * 1000),
                "from_agent": agent_id,
                "to_agent": "gemini" if should_use_gemini else "ollama",
                "msg_type": "plan",
                "intent_tag": task_type or "unknown",
                "content_hash": sha256_text(task_type or "routing") if RKL_LOGGING_AVAILABLE else ""
            })

        if should_use_gemini:
            try:
                response = self.gemini_client.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    agent_id=agent_id,
                    session_id=session_id,
                    turn_id=turn_id,
                    task_type=task_type,
                    **kwargs
                )
                return {
                    'response': response,
                    'model_used': f'gemini ({self.gemini_client.model_name})',
                    'success': True
                }
            except Exception as e:
                logger.warning(f"Gemini failed, falling back to Ollama: {e}")
                # Fall through to Ollama

        # Use Ollama (fallback or default)
        try:
            response = self.ollama_client.generate(
                prompt, system_prompt,
                agent_id=agent_id,
                session_id=session_id,
                turn_id=turn_id
            )
            return {
                'response': response,
                'model_used': f'ollama ({self.ollama_client.model})',
                'success': True
            }
        except Exception as e:
            logger.error(f"Both Gemini and Ollama failed: {e}")
            return {
                'response': '',
                'model_used': 'none',
                'success': False,
                'error': str(e)
            }

    def get_status(self) -> Dict[str, Any]:
        """
        Get status of both model backends.

        Returns:
            Dict with availability status of each model
        """
        return {
            'gemini_available': self.gemini_available,
            'gemini_model': self.gemini_client.model_name if self.gemini_client else None,
            'ollama_available': bool(self.ollama_client),
            'ollama_model': self.ollama_client.model if self.ollama_client else None,
            'preferred_for_critical': self.use_gemini_for
        }


# Convenience function for quick testing
def test_gemini_connection():
    """
    Test Gemini API connection.
    Useful for debugging and verification.
    """
    try:
        client = GeminiClient()
        response = client.generate("Say 'Gemini connection successful!'")
        print(f"✅ Gemini test successful!")
        print(f"Response: {response}")
        return True
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False


if __name__ == "__main__":
    # Run test if executed directly
    print("Testing Gemini connection...")
    test_gemini_connection()
