import httpx
import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self):
        # Fallback to localhost if not specified in environment
        self.base_url = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
        self.token = None
        self.role = None
        self.username = None

    def set_token(self, token: str, role: str, username: str):
        self.token = token
        self.role = role
        self.username = username

    def clear_auth(self):
        self.token = None
        self.role = None
        self.username = None

    def _get_headers(self) -> Dict[str, str]:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def login(self, username: str, password: str) -> bool:
        url = f"{self.base_url}/api/auth/token"
        data = {"username": username, "password": password}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, data=data)
                if response.status_code == 200:
                    res = response.json()
                    self.set_token(res["access_token"], res["role"], username)
                    return True
                return False
        except Exception as e:
            logger.error(f"Login request failed: {e}")
            return False

    async def screen_entity(self, entity_data: dict, frequency: str = "One-time") -> Dict[str, Any]:
        url = f"{self.base_url}/api/screen"
        payload = {"entity": entity_data, "monitoring_frequency": frequency}
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()

    async def get_cases(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/case/all"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()

    async def get_case(self, case_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/case/{case_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()

    async def update_case(self, case_id: str, update_data: dict) -> Dict[str, Any]:
        url = f"{self.base_url}/api/case/{case_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.put(url, json=update_data, headers=self._get_headers())
            response.raise_for_status()
            return response.json()

    async def get_case_audit_logs(self, case_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/case/{case_id}/audit-logs"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()

    async def get_timeline(self, case_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/timeline/{case_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()

    async def get_network(self, case_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/network/{case_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()

    async def get_report_pdf(self, case_id: str) -> bytes:
        url = f"{self.base_url}/api/report/{case_id}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.content

    async def copilot_chat(self, case_id: str, message: str) -> str:
        url = f"{self.base_url}/api/copilot/chat"
        payload = {"case_id": case_id, "message": message}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json().get("answer", "")

    async def subscribe(self, sub_data: dict) -> Dict[str, Any]:
        url = f"{self.base_url}/api/monitor/subscribe"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=sub_data, headers=self._get_headers())
            response.raise_for_status()
            return response.json()

    async def get_subscriptions(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/monitor/subscriptions"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()

    async def get_alerts(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/monitor/alerts"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()

api_client = APIClient()
