from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState
from backend.services.databases.neo4j import neo4j_client
import uuid

class NetworkIntelligenceAgent(BaseAgent):
    def __init__(self):
        super().__init__("network_intelligence")

    async def run(self, state: ScreeningState) -> dict:
        resolved = state["resolved_entity"]
        case_id = state["case_id"]
        
        # Define lists of nodes and edges to update state
        nodes = []
        edges = []
        
        # Primary Entity Node
        primary_id = case_id # Use case ID as unique identifier for the target entity
        nodes.append({
            "id": primary_id,
            "label": resolved["name"],
            "group": "Target",
            "type": resolved["entity_type"],
            "risk_score": 0 # updated later
        })
        
        # We can insert the Primary Entity Node to Neo4j
        await neo4j_client.add_entity_node(
            entity_id=primary_id,
            name=resolved["name"],
            entity_type=resolved["entity_type"],
            country=resolved["country"]
        )

        # ─── Process Relationships ───
        # Directors
        for director in resolved.get("directors", []):
            dir_id = f"dir-{uuid.uuid4().hex[:8]}"
            nodes.append({"id": dir_id, "label": director, "group": "Person", "type": "Individual"})
            edges.append({"from": primary_id, "to": dir_id, "label": "DIRECTOR"})
            
            await neo4j_client.add_entity_node(dir_id, director, "Individual", resolved["country"])
            await neo4j_client.add_relationship(dir_id, primary_id, "DIRECTOR")

        # Shareholders
        for sh in resolved.get("shareholders", []):
            sh_id = f"sh-{uuid.uuid4().hex[:8]}"
            nodes.append({"id": sh_id, "label": sh, "group": "Shareholder", "type": "Company"})
            edges.append({"from": sh_id, "to": primary_id, "label": "SHAREHOLDER"})
            
            await neo4j_client.add_entity_node(sh_id, sh, "Company", resolved["country"])
            await neo4j_client.add_relationship(sh_id, primary_id, "SHAREHOLDER")

        # UBOs (Beneficial Owners)
        for ubo in resolved.get("beneficial_owners", []):
            ubo_id = f"ubo-{uuid.uuid4().hex[:8]}"
            nodes.append({"id": ubo_id, "label": ubo, "group": "BeneficialOwner", "type": "Individual"})
            edges.append({"from": ubo_id, "to": primary_id, "label": "BENEFICIAL_OWNER"})
            
            await neo4j_client.add_entity_node(ubo_id, ubo, "Individual", resolved["country"])
            await neo4j_client.add_relationship(ubo_id, primary_id, "BENEFICIAL_OWNER")

        # Subsidiaries
        for sub in resolved.get("subsidiaries", []):
            sub_id = f"sub-{uuid.uuid4().hex[:8]}"
            nodes.append({"id": sub_id, "label": sub, "group": "Subsidiary", "type": "Company"})
            edges.append({"from": primary_id, "to": sub_id, "label": "SUBSIDIARY"})
            
            await neo4j_client.add_entity_node(sub_id, sub, "Company", resolved["country"])
            await neo4j_client.add_relationship(primary_id, sub_id, "SUBSIDIARY")

        # Parent Company
        if resolved.get("parent_company"):
            parent = resolved["parent_company"]
            parent_id = f"parent-{uuid.uuid4().hex[:8]}"
            nodes.append({"id": parent_id, "label": parent, "group": "ParentCompany", "type": "Company"})
            edges.append({"from": primary_id, "to": parent_id, "label": "PARENT_COMPANY"})
            
            await neo4j_client.add_entity_node(parent_id, parent, "Company", resolved["country"])
            await neo4j_client.add_relationship(primary_id, parent_id, "PARENT_COMPANY")

        # Mapped Articles & Sanctions can be added during those steps
        # Calculate Risk propagation metrics
        # Network risk score formula:
        # direct_risk = sum of event severities / count
        # indirect_risk = risk of parent/subsidiaries / count
        # inherited_risk = risk from shareholders/UBOs
        
        # Update risk scores in nodes
        for node in nodes:
            if node["id"] == primary_id:
                # Primary risk will be set by the risk scoring agent later
                node["risk_score"] = 0
            else:
                node["risk_score"] = 0

        self.logger.info(f"Network Intelligence built corporate network graph for case: {case_id}")
        return {
            "network_nodes": nodes,
            "network_edges": edges
        }
