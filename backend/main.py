import logging
import datetime
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
from pydantic import BaseModel

from backend.config import settings
from backend.services.databases.postgres import get_db, Base, engine, DBUser
from backend.services.databases.neo4j import neo4j_client
from backend.services.monitoring_scheduler import monitoring_scheduler
from backend.api.dependencies import create_access_token, verify_password, get_password_hash
from backend.models.case import Token
from backend.api.routes import screening, cases, timeline, network, reports, copilot, monitoring

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("backend.main")

app = FastAPI(
    title="Project Sentinel API",
    description="AI-Native Financial Crime Intelligence Platform Backend API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wire up routes
app.include_router(screening.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(timeline.router, prefix="/api")
app.include_router(network.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(copilot.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api")

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

    # 2. Seed Default Users
    async with AsyncSession(engine) as session:
        try:
            # Check if users already exist
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

    # 3. Connect to Neo4j
    try:
        await neo4j_client.connect()
    except Exception as e:
        logger.error(f"Could not connect to Neo4j on startup: {e}")

    # 4. Start APScheduler Monitoring
    try:
        monitoring_scheduler.start()
    except Exception as e:
        logger.error(f"Failed to start monitoring scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down resources...")
    await neo4j_client.close()

# Authentication Endpoint
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

# Healthcheck Endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
