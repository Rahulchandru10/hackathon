import json
import logging
from typing import Dict, Any, List
from ollama import AsyncClient
from backend.services.databases.neo4j import neo4j_client

logger = logging.getLogger("sentinel.ingestion")

class GraphIngestionPipeline:
    def __init__(self):
        self.ollama_client = AsyncClient()
        self.model_name = "mistral"

    async def ingest_unstructured_text(self, text_content: str, case_id: str, article_id: str = None) -> Dict[str, Any]:
        """
        Extracts forensic entities from text using Ollama, injects true label structures 
        into Neo4j Aura Cloud using APOC, and connects them back to case context parameters.
        """
        system_prompt = (
            "You are an expert AML (Anti-Money Laundering) and corporate intelligence analyst.\n"
            "Analyze the provided text and extract entities. You MUST categorize their type exactly as one of these labels:\n"
            "- 'Entity' (For companies, corporations, or shell structures)\n"
            "- 'Officer' (For people, directors, shareholders, or ultimate beneficial owners)\n"
            "- 'Intermediary' (For law firms, registration agents, or management boutiques)\n"
            "- 'Address' (For physical locations or registered office addresses)\n\n"
            "CRITICAL: Output your response ONLY as a valid, parsable JSON array of objects. "
            "Do not include markdown blocks, introductory pleasantries, or code wrappers. Just the raw JSON.\n\n"
            "JSON Format Template:\n"
            "[\n"
            "  {\n"
            "    \"source\": \"FALCON MARITIME LTD\",\n"
            "    \"source_type\": \"Entity\",\n"
            "    \"relationship\": \"INTERMEDIARY_OF\",\n"
            "    \"target\": \"MOSSACK FONSECA\",\n"
            "    \"target_type\": \"Intermediary\",\n"
            "    \"risk_impact\": 75\n"
            "  }\n"
            "]"
        )

        user_content = f"Analyze this intelligence brief and extract the graph topology:\n\n{text_content}"

        try:
            logger.info(f"📡 Dispatching payload to Ollama for Case: {case_id}...")
            response = await self.ollama_client.generate(
                model=self.model_name,
                system=system_prompt,
                prompt=user_content,
                options={"temperature": 0.1}
            )
            
            raw_json = response['response'].strip()
            if raw_json.startswith("```json"):
                raw_json = raw_json.replace("```json", "", 1).rstrip("```").strip()
            elif raw_json.startswith("```"):
                raw_json = raw_json.replace("```", "", 1).rstrip("```").strip()

            triplets: List[Dict[str, Any]] = json.loads(raw_json)
            logger.info(f"📊 Extracted {len(triplets)} network vectors from local LLM context.")

            inserted_count = 0
            for item in triplets:
                s_name = item.get("source", "").strip().upper()
                s_type = item.get("source_type", "Entity").strip().capitalize()
                t_name = item.get("target", "").strip().upper()
                t_type = item.get("target_type", "Entity").strip().capitalize()
                
                # Fallback safety validation mappings to match data specifications
                if s_type not in ["Entity", "Officer", "Intermediary", "Address"]: s_type = "Entity"
                if t_type not in ["Entity", "Officer", "Intermediary", "Address"]: t_type = "Entity"
                
                rel = item.get("relationship", "LINKED_TO").strip().upper().replace(" ", "_")
                risk = int(item.get("risk_impact", 40))

                if not s_name or not t_name or s_name == t_name:
                    continue

                # Clean case identifier structure mapping parameter safety checks
                clean_case_id = str(case_id).strip()

                # Dynamic Node & Edge generation utilizing native APOC hooks
                cypher_query = """
                CALL apoc.merge.node([$s_type], {name: $s_name}, {
                    case_id: $clean_case_id, 
                    node_id: apoc.util.md5([$s_name]),
                    type: $s_type,
                    created_at: timestamp()
                }, {}) YIELD node as source
                
                CALL apoc.merge.node([$t_type], {name: $t_name}, {
                    case_id: $clean_case_id, 
                    node_id: apoc.util.md5([$t_name]),
                    type: $t_type,
                    created_at: timestamp()
                }, {}) YIELD node as target
                
                WITH source, target
                CALL apoc.create.relationship(source, $rel, {weight: $risk, article_id: $article_id}, target) YIELD rel as r
                RETURN source, r, target
                """
                
                await neo4j_client.run_query(
                    cypher_query,
                    s_name=s_name, s_type=s_type,
                    t_name=t_name, t_type=t_type,
                    rel=rel, risk=risk, 
                    clean_case_id=clean_case_id, article_id=article_id
                )
                inserted_count += 1

            return {"status": "success", "extracted_relations": len(triplets), "committed_edges": inserted_count}

        except Exception as e:
            logger.error(f"❌ Ingestion pipeline failed: {e}")
            return {"status": "error", "message": str(e)}

ingestion_pipeline = GraphIngestionPipeline()
