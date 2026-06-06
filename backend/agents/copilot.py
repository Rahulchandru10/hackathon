from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState
from backend.services.databases.qdrant import qdrant_client
from backend.services.embeddings import embedding_service
from backend.services.llm import llm_client

class CopilotAgent(BaseAgent):
    def __init__(self):
        super().__init__("copilot")
        self.collection_name = "case_findings"

    async def answer_question(self, case_id: str, question: str, case_context: str = "") -> str:
        """
        Answers questions about a case, optionally using Qdrant vector retrieval.
        """
        # 1. Retrieve relevant vectors from Qdrant if collection exists
        context_docs = []
        try:
            query_vector = embedding_service.get_embedding(question)
            hits = qdrant_client.search_similar(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=3,
                filter_dict={"case_id": case_id}
            )
            for hit in hits:
                payload = hit.get("payload", {})
                context_docs.append(f"Source: {payload.get('title', 'Compliance Document')}\nContent: {payload.get('text', '')}")
        except Exception as e:
            self.logger.error(f"Qdrant RAG retrieval failed: {e}")

        # Assemble prompt context
        retrieved_context = "\n\n".join(context_docs)
        
        prompt = f"""
        You are the AI Investigation Copilot. An analyst is asking a question about Case ID: {case_id}.
        
        Primary Case Context:
        {case_context}

        Retrieved RAG Context (if any):
        {retrieved_context}

        Question:
        {question}

        Provide a precise, factual, compliance-appropriate answer based only on the evidence above. If you don't know, state clearly that the evidence does not specify the answer.
        """
        
        system_prompt = "You are Project Sentinel's AI Investigation Copilot, helping compliance analysts audit financial crime risks."
        
        try:
            return await llm_client.generate_response(prompt, system_prompt=system_prompt)
        except Exception as e:
            return f"Error generating copilot response: {str(e)}"

    async def run(self, state: ScreeningState) -> dict:
        # Copilot operates interactively outside the intake graph,
        # but we implement run as part of BaseAgent interface
        return {}

copilot_agent = CopilotAgent()
