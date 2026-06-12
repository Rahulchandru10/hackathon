import logging
import datetime
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
from pydantic import BaseModel, Field
from typing import List

# Core Configurations & Database Context Layer
from backend.config import settings
from backend.services.databases.postgres import get_db, Base, engine, DBUser, DBCase
from backend.services.databases.neo4j import neo4j_client
from backend.services.monitoring_scheduler import monitoring_scheduler
from backend.api.dependencies import create_access_token, verify_password, get_password_hash
from backend.models.case import Token

# Original Application Core Routers
from backend.api.routes import screening, cases, timeline, network, reports, copilot, monitoring

# Live External Data Provider Infrastructure
from backend.services.news_provider import news_provider
from backend.services.ingestion import ingestion_pipeline

# ─── LOGGING CONFIGURATION ──────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("backend.main")

# ─── INITIALIZE FASTAPI CONTAINER ───────────────────────────────────────────
app = FastAPI(
    title="Project Sentinel API",
    description="AI-Native Financial Crime Intelligence Platform Backend API",
    version="1.0.0"
)

# ─── CORS NETWORK MIDDLEWARE LAYER ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── WIRING ACTIVE ROUTERS MATRIX ───────────────────────────────────────────
app.include_router(screening.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(timeline.router, prefix="/api")
app.include_router(network.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(copilot.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api")

# ─── SERVICE INCEPTION LIFECYCLE HOOKS ──────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing databases and background scheduler...")
    
    # 1. Initialize Postgres Schema
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("PostgreSQL database tables initialized.")
    except Exception as e:
        logger.critical(f"Failed to initialize PostgreSQL tables: {e}")

    # 2. Seed Default Compliance Profiles
    async with AsyncSession(engine) as session:
        try:
            result = await session.execute(select(DBUser).limit(1))
            if not result.scalar_one_or_none():
                logger.info("Seeding default compliance users...")
                default_users = [
                    DBUser(username="analyst", email="analyst@sentinel.local", role="Analyst", hashed_password=get_password_hash("sentinelpass")),
                    DBUser(username="manager", email="manager@sentinel.local", role="Compliance Manager", hashed_password=get_password_hash("sentinelpass")),
                    DBUser(username="mlro", email="mlro@sentinel.local", role="MLRO", hashed_password=get_password_hash("sentinelpass")),
                    DBUser(username="admin", email="admin@sentinel.local", role="Admin", hashed_password=get_password_hash("sentinelpass"))
                ]
                session.add_all(default_users)
                await session.commit()
                logger.info("Default compliance users seeded successfully.")
        except Exception as e:
            logger.error(f"Failed to seed default users: {e}")
            await session.rollback()

    # 3. Establish Neo4j Secure Cloud Tunnel
    try:
        await neo4j_client.connect()
        logger.info("Neo4j database context connection established successfully.")
    except Exception as e:
        logger.error(f"Could not connect to Neo4j on startup: {e}")

    # 4. Start Background APScheduler Task Streams
    try:
        monitoring_scheduler.start()
        logger.info("Monitoring background scheduler engine active.")
    except Exception as e:
        logger.error(f"Failed to start monitoring scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down resources...")
    await neo4j_client.close()

# ─── AUTHENTICATION HANDSHAKE MATRIX ────────────────────────────────────────
@app.post("/api/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    query = select(DBUser).where(DBUser.username == form_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

# ─── CORE SYSTEM HEALTH VIEWS ───────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

# ─── DYNAMIC TRANSFORMATION & PERSISTENCE LAYER ──────────────────────────────
class LiveScreenRequest(BaseModel):
    company_name: str = Field(..., description="Target name sent to news streams")
    case_id: str = Field(..., description="Matching operational case constraint record")

@app.post("/api/screen/live-news-graph")
async def run_live_news_ingestion_pipeline(payload: LiveScreenRequest, db: AsyncSession = Depends(get_db)):
    """
    1. Fetches real-time adverse entries via Newsdata.io matching company filters.
    2. Pipelines data into Ollama and writes entities dynamically to Neo4j.
    3. Saves the live articles to PostgreSQL so 3_results.py reads them instantly!
    """
    try:
        logger.info(f"📰 Initiating live screening traversal matrix for entity: '{payload.company_name}'")
        
        # Step 1: Pull live corporate records from your external news api client provider
        articles = await news_provider.fetch_adverse_corporate_news(payload.company_name)
        
        if not articles:
            logger.info("ℹ️ No streaming adverse media responses returned from global news wire.")
            return {
                "status": "completed", 
                "message": f"No adverse items discovered across media registries.",
                "records_processed": 0,
                "articles": []
            }
            
        processed_count = 0
        formatted_ui_articles = []
        
        # Process up to top 3 matching elements to stay clean inside hackathon latency windows
        for idx, art in enumerate(articles[:3]):
            title_text = art.get('title', '') or 'Untitled External Media Match'
            body_content = art.get('description', '') or art.get('content', '') or art.get('snippet', '')
            source_id = art.get('source_id', 'EXTERNAL_STREAM').upper()
            article_url = art.get('link', 'https://newsdata.io')
            
            text_dump = f"Title: {title_text}\nContext: {body_content}"
            
            # Formulate structured deterministic token prefix keys
            safe_prefix = str(payload.case_id).replace("case-", "")[:4]
            art_id = f"newsdata_{safe_prefix}_{idx}"
            
            # Step 2: Feed strings directly into Ollama model context for Neo4j generation
            logger.info(f"🧠 Parsing raw text dump index [{idx+1}] through Ollama processing pipeline...")
            await ingestion_pipeline.ingest_unstructured_text(
                text_content=text_dump,
                case_id=payload.case_id,
                article_id=art_id
            )
            processed_count += 1
            
            # Inject properties explicitly formatting for the card render utility schema expectations
            formatted_ui_articles.append({
                "title": title_text,
                "source": source_id,
                "source_tier": 1,
                "credibility_score": 95 - (idx * 2),
                "summary": body_content,
                "url": article_url
            })
            
        # Step 3: PERSIST DIRECTLY TO POSTGRESQL FOR DYNAMIC CARD RENDERING
        query = select(DBCase).where(DBCase.id == payload.case_id)
        result = await db.execute(query)
        case_record = result.scalar_one_or_none()
        
        if case_record:
            # Handle column configuration mapping fallback contexts automatically
            if hasattr(case_record, 'articles'):
                case_record.articles = formatted_ui_articles
            else:
                if not case_record.risk_breakdown:
                    case_record.risk_breakdown = {}
                case_record.risk_breakdown["cached_articles"] = formatted_ui_articles
            
            await db.commit()
            logger.info(f"💾 Successfully cached {processed_count} live elements inside Postgres for Case ID {payload.case_id}")

        return {
            "status": "success",
            "records_processed": processed_count,
            "database_target": "Neo4j Aura Cloud 29b956f8",
            "articles": formatted_ui_articles 
        }

    except Exception as e:
        logger.error(f"❌ Real-Time Data Ingestion Layer Halted: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Automated AI screening pipeline encountered an internal execution error: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
