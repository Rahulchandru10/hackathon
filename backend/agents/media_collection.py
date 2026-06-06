import asyncio
from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState
from backend.services.search.serper import serper_service
from backend.services.search.gdelt import gdelt_service

class MediaCollectionAgent(BaseAgent):
    def __init__(self):
        super().__init__("media_collection")

    async def run(self, state: ScreeningState) -> dict:
        queries = state["search_queries"]
        
        # Parallel execution of searches
        tasks = []
        # Run top 5 high-priority queries to keep performance snappy, but query both Serper and GDELT
        target_queries = queries[:6]
        
        for q in target_queries:
            tasks.append(serper_service.search(q, num_results=5))
            tasks.append(gdelt_service.search(q, num_results=5))

        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        raw_articles = []
        seen_urls = set()
        
        for res in results_list:
            if isinstance(res, list):
                for art in res:
                    url = art.get("url")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        raw_articles.append(art)
            elif isinstance(res, Exception):
                self.logger.error(f"Search task encountered exception: {res}")

        self.logger.info(f"Media Collection gathered {len(raw_articles)} unique raw articles.")
        return {"raw_articles": raw_articles}
