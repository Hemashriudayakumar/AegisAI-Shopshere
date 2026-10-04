import json
import logging
from typing import Any, Dict, Optional
import httpx
from app.config import settings
from app.agents.prompt import AGENT_A_SYSTEM_PROMPT
from app.agents.mock_llm import mock_llm_provider

logger = logging.getLogger(__name__)

def check_ollama_alive(base_url: str) -> bool:
    """Fast check to see if Ollama server is running and responsive."""
    try:
        url = f"{base_url.rstrip('/')}/api/tags"
        res = httpx.get(url, timeout=0.8)
        return res.status_code == 200
    except Exception:
        return False

def get_active_ollama_model(base_url: str, preferred: str) -> Optional[str]:
    """Finds the best matching installed model in Ollama."""
    try:
        url = f"{base_url.rstrip('/')}/api/tags"
        res = httpx.get(url, timeout=0.8)
        if res.status_code == 200:
            models = [m.get("name") for m in res.json().get("models", []) if m.get("name")]
            if preferred in models:
                return preferred
            for m in models:
                if "qwen" in m.lower():
                    return m
            if models:
                return models[0]
    except Exception:
        pass
    return preferred

class LLMProvider:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model_name = settings.OLLAMA_MODEL
        self.use_mock = settings.USE_MOCK_LLM_BY_DEFAULT
        self._chat_client = None
        self._resolved_model = None

    def _get_chat_client(self):
        active_model = get_active_ollama_model(self.base_url, self.model_name)
        if self._chat_client is None or self._resolved_model != active_model:
            try:
                from langchain_ollama import ChatOllama
                self._resolved_model = active_model or self.model_name
                self._chat_client = ChatOllama(
                    base_url=self.base_url,
                    model=self._resolved_model,
                    temperature=0.0,
                    format="json",
                    request_timeout=8.0,
                )
            except Exception as e:
                logger.warning(f"Could not initialize ChatOllama client: {e}")
                self._chat_client = None
        return self._chat_client

    def generate_agent_a(
        self,
        customer_message: str,
        conversation_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Calls Qwen via Ollama if available, or immediately uses MockLLMProvider."""
        if self.use_mock or not check_ollama_alive(self.base_url):
            return mock_llm_provider.generate(customer_message, conversation_context)

        client = self._get_chat_client()
        if client is None:
            return mock_llm_provider.generate(customer_message, conversation_context)

        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            messages = [
                SystemMessage(content=AGENT_A_SYSTEM_PROMPT),
                HumanMessage(
                    content=f"Context: {json.dumps(conversation_context or {})}\nCustomer Message: {customer_message}"
                )
            ]
            response = client.invoke(messages)
            content = response.content.strip()
            
            # Parse JSON
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "response" in parsed:
                return parsed
            else:
                return {
                    "response": content,
                    "proposed_action": None
                }
        except Exception as e:
            logger.info(f"Ollama call failed ({e}), using mock provider.")
            return mock_llm_provider.generate(customer_message, conversation_context)

llm_provider = LLMProvider()
