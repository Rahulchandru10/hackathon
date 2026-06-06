import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.screening import ScreeningRequest, ScreeningResponse
from backend.workflow.graph import run_screening_workflow
from backend.services.databases.postgres import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/screen", tags=["screening"])

@router.post("", response_model=ScreeningResponse)
async def screen_entity(payload: ScreeningRequest, db: AsyncSession = Depends(get_db)):
    logger.info(f"Received screening request for: {payload.entity.name}")
    try:
        results = await run_screening_workflow(
            entity=payload.entity,
            monitoring_frequency=payload.monitoring_frequency
        )
        return results
    except Exception as e:
        logger.error(f"Screening workflow failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Screening workflow failed: {str(e)}"
        )
