# Project Sentinel — AI-Native Financial Crime Intelligence Platform

Project Sentinel is an enterprise-grade, local-first Financial Crime Intelligence Platform designed for compliance analysts. It integrates adverse media screening, AML risk profiling, PEP/sanctions matching, corporate network visualization, continuous monitoring, and an AI investigation copilot.

---

## Architecture

The system utilizes an orchestrator powered by **LangGraph** executing an **18-Agent workflow**:
1. **Entity Intake Agent**: Validation of inputs and warnings on sparse data context.
2. **Entity Resolution Agent**: Match classification checking name aliases, registration number, country and websites.
3. **Search Query Agent**: Multi-lingual keywords generator.
4. **Media Collection Agent**: Fetches results concurrently from Serper and GDELT.
5. **Duplicate Detection Agent**: Groups similar news using BGE-M3 embeddings.
6. **Source Credibility Agent**: Scores publishing domains 0-100 on 5 credibility axes.
7. **Event Extraction Agent**: Extracts structured financial crime events from adverse articles.
8. **False Positive Agent**: Disambiguates mismatches.
9. **Timeline Agent**: Orders events chronologically.
10. **Network Intelligence Agent**: Builds entity connection mappings in Neo4j and propagates risk.
11. **PEP Screening Agent**: Checks Politically Exposed Persons registries.
12. **Sanctions Screening Agent**: Mapped against OFAC, EU, UN sanctions.
13. **Risk Scoring Agent**: Computes composite risk dial values (0-100).
14. **Recommendation Agent**: Resolves decisions (CLEAR, ESCALATE, REJECT).
15. **Explainability Agent**: Generates textual audit reasoning.
16. **Regulator QA Agent**: Evaluates case file compliance and challenges conclusions.
17. **Monitoring Agent**: Delivers scheduled delta alerts feed.
18. **AI Investigation Copilot**: RAG chat assistance over case files using Qdrant.

---

## Technology Stack & Ports

| Service | Technology | Internal Port | External Port |
|---|---|---|---|
| Frontend | Streamlit | 8501 | **8501** |
| Backend | FastAPI / Uvicorn | 8000 | **8000** |
| Database | PostgreSQL | 5432 | **5432** |
| Graph Database | Neo4j Community | 7474 / 7687 | **7474 / 7687** |
| Vector Database | Qdrant | 6333 / 6334 | **6333 / 6334** |
| Cache Store | Redis | 6379 | **6379** |
| LLM Host | Ollama (Qwen3:14B) | 11434 | **11434** |

---

## Local Setup

1. Copy `.env.example` to `.env` and configure your keys (e.g. `SERPER_API_KEY` for live web search).
2. Start the Docker services stack:
   ```bash
   docker-compose up --build -d
   ```
3. Initial migrations and default users seeding are automatically run on startup.
4. Access the Streamlit frontend panel:
   ```
   http://localhost:8501
   ```

### Default Credentials
For validation, log in using any of the seeded roles below:
- **analyst** (password: `sentinelpass`) - Analyst case review & copilot.
- **manager** (password: `sentinelpass`) - Assignment, audit & logs.
- **mlro** (password: `sentinelpass`) - Sign-off decisioning.
- **admin** (password: `sentinelpass`) - Settings.

---

## Testing

Run unit and integration suites using `pytest`:
```bash
# Execute unit test suite
pytest backend/tests/unit -v

# Execute API integration validations
pytest backend/tests/integration -v
```
