import logging
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.agents.copilot import copilot_agent
from backend.services.databases.postgres import get_db, DBCase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/copilot", tags=["copilot"])

class ChatRequest(BaseModel):
    case_id: str
    message: str

class ChatResponse(BaseModel):
    answer: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_copilot(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    logger.info(f"Received copilot question for case {payload.case_id}: {payload.message}")
    
    # Fetch case context to pass to agent
    query = select(DBCase).where(DBCase.id == payload.case_id)
    res = await db.execute(query)
    c = res.scalar_one_or_none()
    
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {payload.case_id} not found."
        )
        
    case_context = (
        f"Target Legal Name: {c.entity_name}\n"
        f"Entity Type: {c.entity_type}\n"
        f"Country: {c.country}\n"
        f"Risk Score: {c.risk_score}/100\n"
        f"Recommendation: {c.recommendation}\n"
        f"Justification: {c.recommendation_justification}"
    )

    try:
        answer = await copilot_agent.answer_question(
            case_id=payload.case_id,
            question=payload.message,
            case_context=case_context
        )
        return ChatResponse(answer=answer)
    except Exception as e:
        logger.error(f"Copilot failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Copilot interaction failed: {str(e)}"
        )
