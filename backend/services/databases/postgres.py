import datetime
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from backend.config import settings

# Resolve DB URL: SQLite for local mode, PostgreSQL for production/docker
DATABASE_URL = settings.get_db_url()

# SQLite requires check_same_thread=False for async use
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_async_engine(DATABASE_URL, echo=False, connect_args=connect_args)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class DBCase(Base):
    __tablename__ = "cases"
    id = Column(String(100), primary_key=True, index=True)
    entity_name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50))
    country = Column(String(100))
    industry = Column(String(100))
    website = Column(String(255))
    registration_number = Column(String(100))
    # JSON replaces ARRAY(Text) — works in both SQLite and PostgreSQL
    aliases = Column(JSON, default=list)
    parent_company = Column(String(255))
    subsidiaries = Column(JSON, default=list)
    directors = Column(JSON, default=list)
    shareholders = Column(JSON, default=list)
    beneficial_owners = Column(JSON, default=list)
    status = Column(String(50), default="OPEN")
    risk_score = Column(Integer, default=0)
    risk_breakdown = Column(JSON, default=dict)
    recommendation = Column(String(100))
    recommendation_justification = Column(Text)
    regulator_qa_status = Column(String(50), default="PENDING")
    regulator_qa_deficiencies = Column(JSON, default=list)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    articles = relationship("DBArticle", back_populates="case", cascade="all, delete-orphan")
    events = relationship("DBEvent", back_populates="case", cascade="all, delete-orphan")


class DBArticle(Base):
    __tablename__ = "articles"
    id = Column(String(100), primary_key=True, index=True)
    case_id = Column(String(100), ForeignKey("cases.id", ondelete="CASCADE"))
    title = Column(String(500), nullable=False)
    url = Column(Text, nullable=False)
    source = Column(String(255), nullable=False)
    source_tier = Column(Integer)
    credibility_score = Column(Integer)
    publish_date = Column(DateTime)
    summary = Column(Text)
    content = Column(Text)
    language = Column(String(10), default="en")
    cluster_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("DBCase", back_populates="articles")


class DBEvent(Base):
    __tablename__ = "events"
    id = Column(String(100), primary_key=True, index=True)
    case_id = Column(String(100), ForeignKey("cases.id", ondelete="CASCADE"))
    article_id = Column(String(100), ForeignKey("articles.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(100), nullable=False)
    severity = Column(Integer)
    description = Column(Text)
    detected_date = Column(String(50))
    location = Column(String(255))
    entities_involved = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("DBCase", back_populates="events")


class DBSubscription(Base):
    __tablename__ = "monitoring_subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    entity_name = Column(String(255), nullable=False)
    entity_type = Column(String(50))
    country = Column(String(100))
    industry = Column(String(100))
    website = Column(String(255))
    registration_number = Column(String(100))
    frequency = Column(String(50), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    last_checked = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class DBAlert(Base):
    __tablename__ = "alerts"
    id = Column(String(100), primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("monitoring_subscriptions.id", ondelete="CASCADE"), nullable=True)
    case_id = Column(String(100), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True)
    alert_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class DBAuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(100), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
