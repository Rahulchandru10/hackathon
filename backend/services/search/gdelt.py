import logging
import urllib.parse
import httpx
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class GDELTSearchService:
    def __init__(self):
        self.endpoint = "https://api.gdeltproject.org/api/v2/doc/doc"

    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        # GDELT API documentation: https://blog.gdeltproject.org/gdelt-doc-2-0-api-developer-guide/
        # Format query for GDELT (cannot have complex double quotes or AND/OR inside quotes)
        safe_query = query.replace('"', '').replace("AND", "").replace("OR", "")
        
        # Build request params
        params = {
            "query": safe_query,
            "mode": "ArtList",
            "format": "JSON",
            "maxrecords": num_results,
            "timespan": "365d" # Last 1 year
        }
        
        url = f"{self.endpoint}?{urllib.parse.urlencode(params)}"
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    articles = []
                    for item in data.get("articles", []):
                        articles.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("socialimage", ""), # GDELT returns socialimage, source country etc.
                            "source": item.get("domain", ""),
                            "publish_date": item.get("seendate", None)
                        })
                    return articles
                else:
                    logger.warning(f"GDELT API returned status {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"GDELT query failed: {e}")
            return []

gdelt_service = GDELTSearchService()
