import logging
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List
from backend.models.case import CaseResponse, CaseUpdate, AuditLogResponse
from backend.services.databases.postgres import get_db, DBCase, DBAuditLog, DBUser
from backend.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/case", tags=["cases"])

@router.get("/all", response_model=List[CaseResponse])
async def get_all_cases(db: AsyncSession = Depends(get_db)):
    query = select(DBCase).order_by(DBCase.created_at.desc())
    result = await db.execute(query)
    cases = result.scalars().all()
    # Format output models
    output = []
    for c in cases:
        output.append(
            CaseResponse(
                id=c.id,
                entity={
                    "id": c.id,
                    "name": c.entity_name,
                    "entity_type": c.entity_type,
                    "country": c.country,
                    "industry": c.industry,
                    "website": c.website,
                    "registration_number": c.registration_number,
                    "aliases": c.aliases or [],
                    "parent_company": c.parent_company,
                    "subsidiaries": c.subsidiaries or [],
                    "directors": c.directors or [],
                    "shareholders": c.shareholders or [],
                    "beneficial_owners": c.beneficial_owners or []
                },
                status=c.status,
                risk_score=c.risk_score,
                risk_breakdown=c.risk_breakdown,
                recommendation=c.recommendation,
                recommendation_justification=c.recommendation_justification,
                regulator_qa_status=c.regulator_qa_status,
                regulator_qa_deficiencies=c.regulator_qa_deficiencies or [],
                assigned_to=c.assigned_to,
                created_at=c.created_at,
                updated_at=c.updated_at
            )
        )
    return output

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)):
    query = select(DBCase).where(DBCase.id == case_id)
    result = await db.execute(query)
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found."
        )
    return CaseResponse(
        id=c.id,
        entity={
            "id": c.id,
            "name": c.entity_name,
            "entity_type": c.entity_type,
            "country": c.country,
            "industry": c.industry,
            "website": c.website,
            "registration_number": c.registration_number,
            "aliases": c.aliases or [],
            "parent_company": c.parent_company,
            "subsidiaries": c.subsidiaries or [],
            "directors": c.directors or [],
            "shareholders": c.shareholders or [],
            "beneficial_owners": c.beneficial_owners or []
        },
        status=c.status,
        risk_score=c.risk_score,
        risk_breakdown=c.risk_breakdown,
        recommendation=c.recommendation,
        recommendation_justification=c.recommendation_justification,
        regulator_qa_status=c.regulator_qa_status,
        regulator_qa_deficiencies=c.regulator_qa_deficiencies or [],
        assigned_to=c.assigned_to,
        created_at=c.created_at,
        updated_at=c.updated_at
    )

@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: str, 
    payload: CaseUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    query = select(DBCase).where(DBCase.id == case_id)
    result = await db.execute(query)
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found."
        )
        
    update_data = payload.dict(exclude_unset=True)
    if "notes" in update_data:
        # Notes is stored as recommendation justification or added to audit logs
        notes = update_data.pop("notes")
        audit = DBAuditLog(
            case_id=case_id,
            user_id=current_user.id,
            action="ADD_NOTE",
            details=f"Compliance Analyst Note added: {notes}"
        )
        db.add(audit)
        
    if update_data:
        for key, val in update_data.items():
            setattr(c, key, val)
        c.updated_at = datetime.datetime.utcnow()
        
    # Log audit entry for modification
    audit = DBAuditLog(
        case_id=case_id,
        user_id=current_user.id,
        action="UPDATE_CASE",
        details=f"Case updated attributes: {', '.join(update_data.keys())}"
    )
    db.add(audit)
    
    await db.commit()
    return await get_case(case_id, db)

@router.get("/{case_id}/audit-logs", response_model=List[AuditLogResponse])
async def get_case_audit_logs(case_id: str, db: AsyncSession = Depends(get_db)):
    query = select(DBAuditLog).where(DBAuditLog.case_id == case_id).order_by(DBAuditLog.timestamp.desc())
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Enrich user names
    output = []
    for log in logs:
        username = "System"
        if log.user_id:
            u_query = select(DBUser).where(DBUser.id == log.user_id)
            u_res = await db.execute(u_query)
            u = u_res.scalar_one_or_none()
            if u:
                username = u.username
        output.append(
            AuditLogResponse(
                id=log.id,
                case_id=log.case_id,
                user_id=log.user_id,
                username=username,
                action=log.action,
                details=log.details,
                timestamp=log.timestamp
            )
        )
    return output
