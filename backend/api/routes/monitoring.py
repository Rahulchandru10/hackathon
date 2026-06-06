import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from backend.models.alerts import SubscriptionCreate, SubscriptionResponse, AlertResponse
from backend.services.databases.postgres import get_db, DBSubscription, DBAlert
from backend.api.dependencies import get_current_user, DBUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitor", tags=["monitoring"])

@router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe_entity(
    payload: SubscriptionCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} subscribing to {payload.entity_name}")
    try:
        db_sub = DBSubscription(
            entity_name=payload.entity_name,
            entity_type=payload.entity_type,
            country=payload.country,
            industry=payload.industry,
            website=payload.website,
            registration_number=payload.registration_number,
            frequency=payload.frequency,
            created_by=current_user.id
        )
        db.add(db_sub)
        await db.commit()
        await db.refresh(db_sub)
        return db_sub
    except Exception as e:
        logger.error(f"Subscription creation failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subscription failed: {str(e)}"
        )

@router.get("/subscriptions", response_model=List[SubscriptionResponse])
async def get_subscriptions(db: AsyncSession = Depends(get_db)):
    query = select(DBSubscription)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(db: AsyncSession = Depends(get_db)):
    query = select(DBAlert).order_by(DBAlert.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()
