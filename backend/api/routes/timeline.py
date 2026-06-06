import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from backend.models.events import EventModel
from backend.services.databases.postgres import get_db, DBEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/timeline", tags=["timeline"])

@router.get("/{case_id}", response_model=List[EventModel])
async def get_case_timeline(case_id: str, db: AsyncSession = Depends(get_db)):
    query = select(DBEvent).where(DBEvent.case_id == case_id).order_by(DBEvent.detected_date.asc())
    result = await db.execute(query)
    events = result.scalars().all()
    
    output = []
    for ev in events:
        output.append(
            EventModel(
                id=ev.id,
                case_id=ev.case_id,
                article_id=ev.article_id,
                event_type=ev.event_type,
                severity=ev.severity,
                description=ev.description,
                detected_date=ev.detected_date,
                location=ev.location,
                entities_involved=ev.entities_involved or []
            )
        )
    return output
