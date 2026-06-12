import httpx
import logging
from typing import List, Dict, Any

logger = logging.getLogger("sentinel.news")

class NewsdataIOProvider:
    def __init__(self):
        # Using your live validated token string
        self.api_key = "pub_66baed91ed0e4ab88182600c17a9cafb"
        self.base_url = "https://newsdata.io/api/1/news"

    async def fetch_adverse_corporate_news(self, search_query: str) -> List[Dict[str, Any]]:
        """
        Pings newsdata.io to catch high-impact adverse corporate events.
        """
        # Formulate query params looking for regulatory enforcement triggers
        combined_query = f'"{search_query}" AND (fraud OR "money laundering" OR sanctions OR corruption)'
        
        params = {
            "apikey": self.api_key,
            "q": combined_query,
            "language": "en"
        }

        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"📰 Querying live news stream for target: '{search_query}'...")
                response = await client.get(self.base_url, params=params, timeout=15.0)
                
                if response.status_code != 200:
                    logger.error(f"Newsdata API Error ({response.status_code}): {response.text}")
                    return []
                
                data = response.json()
                articles = data.get("results", [])
                logger.info(f"✅ Successfully matched {len(articles)} active news briefs across global indices.")
                return articles

            except Exception as e:
                logger.error(f"Failed to query news provider matrix: {e}")
                return []

news_provider = NewsdataIOProvider()
