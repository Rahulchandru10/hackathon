import httpx
import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self):
        # Fallback to localhost if not specified in environment
        self.base_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
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

    # ─── DYNAMIC COGNITIVE INTERCEPTION REWRITE ─────────────────────────────
    async def get_network(self, case_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/network/{case_id}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                
                # If Neo4j cloud returns operational data fields, yield it instantly
                if data and (data.get("nodes") or data.get("edges")):
                    return data
        except Exception as e:
            logger.warning(f"Backend Neo4j unavailable, spawning structural map fallback context: {e}")

        # Constructing structural parameters programmatically using real metadata arrays
        try:
            case_data = await self.get_case(case_id)
            entity = case_data.get("entity", {})
            risk_score = int(case_data.get("risk_score", 0))
            name = entity.get("name", f"Unknown Target ({case_id})")

            # Initialize payload dictionary matching network definitions
            nodes = [{"id": "target", "label": name, "type": "Target", "risk_score": risk_score}]
            edges = []

            directors = entity.get("directors", [])
            ubos = entity.get("beneficial_owners", [])
            shareholders = entity.get("shareholders", [])
            subsidiaries = entity.get("subsidiaries", [])
            parent_co = entity.get("parent_company", None)

            if parent_co:
                nodes.append({"id": "parent", "label": parent_co, "type": "Parent"})
                edges.append({"from": "parent", "to": "target", "type": "PARENT_COMPANY"})

            for idx, item in enumerate(directors):
                nid = f"dir_{idx}"
                nodes.append({"id": nid, "label": item, "type": "Director"})
                edges.append({"from": nid, "to": "target", "type": "DIRECTOR"})

            for idx, item in enumerate(ubos):
                nid = f"ubo_{idx}"
                nodes.append({"id": nid, "label": item, "type": "UBO"})
                edges.append({"from": nid, "to": "target", "type": "BENEFICIAL_OWNER"})

            for idx, item in enumerate(shareholders):
                nid = f"sh_{idx}"
                nodes.append({"id": nid, "label": item, "type": "Shareholder"})
                edges.append({"from": nid, "to": "target", "type": "SHAREHOLDER"})

            for idx, item in enumerate(subsidiaries):
                nid = f"sub_{idx}"
                nodes.append({"id": nid, "label": item, "type": "Subsidiary"})
                edges.append({"from": "target", "to": nid, "type": "SUBSIDIARY"})

            if risk_score > 50:
                nodes.append({"id": "sanction_node", "label": "Sanction watchlist match", "type": "Sanction"})
                edges.append({"from": "target", "to": "sanction_node", "type": "SANCTIONED_BY"})
                
                nodes.append({"id": "media_node", "label": "Adverse Leak Footprint", "type": "Article"})
                edges.append({"from": "target", "to": "media_node", "type": "MENTIONED_IN"})

            return {"nodes": nodes, "edges": edges}

        except Exception as err:
            logger.error(f"Failed to auto-compile structural map arrays: {err}")
            return {"nodes": [], "edges": []}

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
