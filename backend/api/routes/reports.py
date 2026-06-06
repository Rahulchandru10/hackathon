import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.services.databases.postgres import get_db, DBCase, DBArticle, DBEvent
from backend.services.pdf_generator import PDFReportGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["reports"])

@router.get("/{case_id}")
async def download_pdf_report(case_id: str, db: AsyncSession = Depends(get_db)):
    logger.info(f"Generating PDF report for case: {case_id}")
    
    # Fetch Case info
    case_query = select(DBCase).where(DBCase.id == case_id)
    case_res = await db.execute(case_query)
    c = case_res.scalar_one_or_none()
    
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found."
        )

    # Fetch associated articles and events
    art_query = select(DBArticle).where(DBArticle.case_id == case_id)
    art_res = await db.execute(art_query)
    articles = art_res.scalars().all()
    
    ev_query = select(DBEvent).where(DBEvent.case_id == case_id)
    ev_res = await db.execute(ev_query)
    events = ev_res.scalars().all()

    # Match Watchlists Mock PEP/Sanctions matches based on case risk score for visualization in PDF
    pep_matches = []
    sanctions_matches = []
    if c.risk_score > 50:
        # Simulate PEP / Sanction match details for PDF inclusion if high risk
        pep_matches.append({
            "entity_name": c.entity_name,
            "confidence": 0.85,
            "role": "Target Entity Associate / PEP Link",
            "country": c.country or "Global",
            "justification": "Significant media alignment with high-ranking regional officers."
        })
    if c.risk_score > 75:
        sanctions_matches.append({
            "entity_name": c.entity_name,
            "confidence": 0.90,
            "watchlist": "OFAC SDN, EU Consolidated Watchlist",
            "justification": "Target assets flagged on designated international commerce restriction watchlists."
        })

    # Prepare data payload for PDF generator
    case_data = {
        "entity_name": c.entity_name,
        "entity_type": c.entity_type,
        "country": c.country,
        "industry": c.industry,
        "website": c.website,
        "registration_number": c.registration_number,
        "aliases": c.aliases,
        "parent_company": c.parent_company,
        "subsidiaries": c.subsidiaries,
        "directors": c.directors,
        "shareholders": c.shareholders,
        "beneficial_owners": c.beneficial_owners,
        "risk_score": c.risk_score,
        "risk_breakdown": c.risk_breakdown,
        "recommendation": c.recommendation,
        "recommendation_justification": c.recommendation_justification,
        "regulator_qa_status": c.regulator_qa_status,
        "regulator_qa_deficiencies": c.regulator_qa_deficiencies or [],
        "articles": [{"title": a.title, "source": a.source, "credibility_score": a.credibility_score, "source_tier": a.source_tier, "summary": a.summary} for a in articles],
        "events": [{"detected_date": e.detected_date, "event_type": e.event_type, "severity": e.severity, "description": e.description} for e in events],
        "pep_matches": pep_matches,
        "sanctions_matches": sanctions_matches
    }

    try:
        pdf_bytes = PDFReportGenerator.generate_case_pdf(case_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=sentinel-report-{case_id}.pdf"}
        )
    except Exception as e:
        logger.error(f"Failed to generate report PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )
