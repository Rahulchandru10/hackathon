import logging
import httpx
import json
import asyncio
from typing import Optional, Dict, Any, List
from backend.config import settings

logger = logging.getLogger(__name__)

class OllamaLLMClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    def _get_mock_response(self, prompt: str, json_mode: bool) -> str:
        if json_mode:
            prompt_lower = prompt.lower()
            if "false positive" in prompt_lower:
                return json.dumps({
                    "is_false_positive": False,
                    "justification": "The event lists a match related to the target entity profile."
                })
            elif "regulatory auditor" in prompt_lower or "deficiencies" in prompt_lower:
                return json.dumps({
                    "status": "PASS",
                    "deficiencies": []
                })
            elif "resolution" in prompt_lower or "match_type" in prompt_lower:
                return json.dumps({
                    "match_type": "Exact Match",
                    "confidence": 0.9,
                    "justification": "Matches matching name, country, and identifiers."
                })
            elif "extract any financial crime" in prompt_lower or "events" in prompt_lower:
                return json.dumps({
                    "events": [
                        {
                            "event_type": "Litigation",
                            "severity": 60,
                            "description": "Legal proceedings matching regulatory filings and news reports.",
                            "detected_date": "2026-04-10",
                            "location": "US",
                            "entities_involved": ["Target Entity"]
                        }
                    ]
                })
            else:
                return "{}"
        else:
            prompt_lower = prompt.lower()
            if "recommendation" in prompt_lower:
                return "The proposed action is recommended based on the entity risk assessment, warning signals, and compliance policy constraints. Analysts should perform enhanced due diligence (EDD) to confirm entity details."
            elif "explainability" in prompt_lower:
                return """# Risk Score Explanation Report

## Executive Risk Summary
The target entity has been assessed with a composite risk score based on the matching compliance risk parameters.

## Risk Drivers
- Adverse Media: Checked and verified.
- Sanctions / PEP: Database cross-references performed.

## Auditability Note
Resolution confidence is moderate-high. Sources evaluated are verified tier-1/tier-2 compliance databases."""
            else:
                return "Hello! I am your AI compliance copilot. I am running in Local Mock Mode since Ollama is offline. How can I help you with this screening case?"

    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None, json_mode: bool = False, temperature: float = 0.2, retries: int = 3) -> str:
        # Force Mock LLM ONLY if explicitly requested by the environment configurations
        if settings.FORCE_MOCK_LLM:
            logger.info("FORCE_MOCK_LLM is enabled. Returning mock response instantly...")
            return self._get_mock_response(prompt, json_mode)

        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt
            
        # Commented out to allow reasoning models to output thinking text before JSON:
        # if json_mode:
        #     payload["format"] = "json"

        local_timeout = 120.0 if settings.LOCAL_MODE else 180.0
        max_retries = 1 if settings.LOCAL_MODE else retries

        # Attempt connection directly to your live background Ollama service engine
        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=local_timeout) as client:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        res_json = response.json()
                        return res_json.get("response", "").strip()
                    else:
                        logger.warning(f"Ollama returned status {response.status_code} (attempt {attempt}/{max_retries})")
            except Exception as e:
                logger.error(f"Ollama call exception: {e} (attempt {attempt}/{max_retries})")
            
            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)
        
        # --- FIXED LOGIC GAP HERE ---
        # Fall back to your mock data engine ONLY if the connection attempts actively timed out or failed.
        if settings.LOCAL_MODE:
            logger.warning("⚠️ Ollama connection timed out or is completely unreachable. Falling back to mock data arrays...")
            return self._get_mock_response(prompt, json_mode)

        raise RuntimeError("Ollama LLM call failed after all retries.")

    async def generate_structured(self, prompt: str, system_prompt: Optional[str] = None, schema_desc: Optional[str] = None) -> Dict[str, Any]:
        """
        Calls Ollama in JSON mode and returns a parsed dictionary.
        """
        full_prompt = prompt
        if schema_desc:
            full_prompt = f"{prompt}\n\nYou must return valid JSON that conforms to the following schema:\n{schema_desc}"
            
        res_str = await self.generate_response(full_prompt, system_prompt=system_prompt, json_mode=True)
        try:
            return json.loads(res_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama JSON response: {res_str}. Error: {e}")
            # Try to extract JSON from markdown wrappers if any
            import re
            match = re.search(r"\{.*\}", res_str, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Ollama did not return valid JSON: {res_str}")

llm_client = OllamaLLMClient()
