import logging
from neo4j import AsyncGraphDatabase
from backend.config import settings

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        self._driver = None

    async def connect(self):
        if not self._driver:
            try:
                self._driver = AsyncGraphDatabase.driver(
                    self.uri, 
                    auth=(self.user, self.password)
                )
                # Verify connectivity
                await self._driver.verify_connectivity()
                logger.info("Successfully connected to Neo4j database.")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                self._driver = None

    async def close(self):
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Closed Neo4j connection.")

    async def run_query(self, query: str, parameters: dict = None):
        if not self._driver:
            await self.connect()
        if not self._driver:
            logger.warning("Neo4j driver not initialized. Skipping query.")
            return []
        
        async with self._driver.session() as session:
            try:
                result = await session.run(query, parameters or {})
                records = await result.data()
                return records
            except Exception as e:
                logger.error(f"Neo4j query execution failed: {e}")
                raise e

    async def add_entity_node(self, entity_id: str, name: str, entity_type: str, country: str = None, risk_score: int = 0):
        query = """
        MERGE (e:Entity {id: $id})
        SET e.name = $name,
            e.type = $type,
            e.country = $country,
            e.risk_score = $risk_score,
            e.updated_at = timestamp()
        RETURN e
        """
        # Also add more specific labels based on type
        label = "Company" if entity_type == "Company" else "Person"
        type_query = f"""
        MATCH (e:Entity {{id: $id}})
        SET e:{label}
        """
        await self.run_query(query, {"id": entity_id, "name": name, "type": entity_type, "country": country, "risk_score": risk_score})
        await self.run_query(type_query, {"id": entity_id})

    async def add_relationship(self, from_id: str, to_id: str, rel_type: str, props: dict = None):
        # Clean the rel_type string to prevent injection
        allowed_rels = ["DIRECTOR", "SHAREHOLDER", "BENEFICIAL_OWNER", "SUBSIDIARY", "PARENT_COMPANY", "SANCTIONED_BY", "MENTIONED_IN"]
        if rel_type not in allowed_rels:
            raise ValueError(f"Invalid relationship type: {rel_type}")

        query = f"""
        MATCH (a:Entity {{id: $from_id}})
        MATCH (b:Entity {{id: $to_id}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $props
        RETURN r
        """
        await self.run_query(query, {"from_id": from_id, "to_id": to_id, "props": props or {}})

    async def add_article_relationship(self, entity_id: str, article_id: str, article_title: str, url: str, credibility_score: int):
        # Create article node and connect it
        create_article_query = """
        MERGE (a:Article {id: $article_id})
        SET a.title = $title,
            a.url = $url,
            a.credibility_score = $credibility,
            a.updated_at = timestamp()
        """
        rel_query = """
        MATCH (e:Entity {id: $entity_id})
        MATCH (a:Article {id: $article_id})
        MERGE (e)-[r:MENTIONED_IN]->(a)
        RETURN r
        """
        await self.run_query(create_article_query, {"article_id": article_id, "title": article_title, "url": url, "credibility": credibility_score})
        await self.run_query(rel_query, {"entity_id": entity_id, "article_id": article_id})

    async def add_sanction_relationship(self, entity_id: str, sanction_id: str, watchlist: str, justification: str):
        create_sanction_query = """
        MERGE (s:Sanction {id: $sanction_id})
        SET s.watchlist = $watchlist,
            s.justification = $justification,
            s.updated_at = timestamp()
        """
        rel_query = """
        MATCH (e:Entity {id: $entity_id})
        MATCH (s:Sanction {id: $sanction_id})
        MERGE (e)-[r:SANCTIONED_BY]->(s)
        RETURN r
        """
        await self.run_query(create_sanction_query, {"sanction_id": sanction_id, "watchlist": watchlist, "justification": justification})
        await self.run_query(rel_query, {"entity_id": entity_id, "sanction_id": sanction_id})

    async def get_network(self, entity_id: str, max_depth: int = 2):
        query = """
        MATCH (e:Entity {id: $entity_id})
        CALL apoc.path.spanningTree(e, {
            maxLevel: $max_depth,
            relationshipFilter: "DIRECTOR>|SHAREHOLDER>|BENEFICIAL_OWNER>|SUBSIDIARY>|PARENT_COMPANY>|SANCTIONED_BY>|MENTIONED_IN>",
            labelFilter: "+Entity|+Sanction|+Article"
        })
        YIELD path
        RETURN path
        """
        # If apoc is not available, run a standard matching fallback:
        fallback_query = """
        MATCH p=(e:Entity {id: $entity_id})-[r*1..2]-(other)
        RETURN p LIMIT 50
        """
        try:
            return await self.run_query(query, {"entity_id": entity_id, "max_depth": max_depth})
        except Exception:
            logger.info("Spanning tree search failed or APOC missing, using standard query path fallback.")
            return await self.run_query(fallback_query, {"entity_id": entity_id})

neo4j_client = Neo4jClient()
