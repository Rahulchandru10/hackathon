import io
import logging
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PDFReportGenerator:
    @staticmethod
    def generate_case_pdf(case_data: Dict[str, Any]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles for professional aesthetic
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#1A2B4C'),
            spaceAfter=15
        )
        
        h1_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#1A2B4C'),
            spaceBefore=15,
            spaceAfter=8,
            keepWithNext=True
        )

        h2_style = ParagraphStyle(
            'SubSectionHeader',
            parent=styles['Heading3'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#2E4057'),
            spaceBefore=10,
            spaceAfter=5,
            keepWithNext=True
        )

        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6
        )

        bullet_style = ParagraphStyle(
            'ReportBullet',
            parent=body_style,
            leftIndent=15,
            bulletIndent=5,
            spaceAfter=4
        )

        meta_label_style = ParagraphStyle(
            'MetaLabel',
            parent=body_style,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1A2B4C')
        )

        story = []

        # ─── HEADER SECTION ───
        story.append(Paragraph("PROJECT SENTINEL", title_style))
        story.append(Paragraph("Financial Crime Intelligence Report", ParagraphStyle('Sub', parent=body_style, fontSize=12, textColor=colors.HexColor('#666666'))))
        story.append(Spacer(1, 15))
        
        # Horizontal Rule
        rule = Table([[""]], colWidths=[530], rowHeights=[2])
        rule.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1A2B4C')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(rule)
        story.append(Spacer(1, 15))

        # ─── 1. EXECUTIVE SUMMARY ───
        story.append(Paragraph("1. Executive Summary", h1_style))
        entity_name = case_data.get('entity_name', 'Unknown')
        risk_score = case_data.get('risk_score', 0)
        risk_level = "LOW"
        if risk_score > 75:
            risk_level = "CRITICAL"
        elif risk_score > 50:
            risk_level = "HIGH"
        elif risk_score > 20:
            risk_level = "MEDIUM"

        summary_text = (
            f"This compliance screening intelligence report evaluates the financial crime risk profile for "
            f"<b>{entity_name}</b>. Based on comprehensive analysis of adverse media, sanctions watchlists, "
            f"and corporate networks, the target entity is assigned an overall risk score of <b>{risk_score}/100 ({risk_level})</b>. "
            f"The final automated recommendation is <b>{case_data.get('recommendation', 'REQUIRES_HUMAN_REVIEW')}</b>."
        )
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 10))

        # ─── 2. ENTITY PROFILE ───
        story.append(Paragraph("2. Entity Profile", h1_style))
        profile_data = [
            [Paragraph("Attribute", meta_label_style), Paragraph("Value", meta_label_style)],
            [Paragraph("Entity Name", body_style), Paragraph(entity_name, body_style)],
            [Paragraph("Type", body_style), Paragraph(case_data.get('entity_type', 'Unknown'), body_style)],
            [Paragraph("Country", body_style), Paragraph(case_data.get('country', 'N/A'), body_style)],
            [Paragraph("Industry", body_style), Paragraph(case_data.get('industry', 'N/A'), body_style)],
            [Paragraph("Website", body_style), Paragraph(case_data.get('website', 'N/A'), body_style)],
            [Paragraph("Registration No.", body_style), Paragraph(case_data.get('registration_number', 'N/A'), body_style)],
            [Paragraph("Aliases", body_style), Paragraph(", ".join(case_data.get('aliases', []) or ["None"]), body_style)],
            [Paragraph("Parent Company", body_style), Paragraph(case_data.get('parent_company', 'None'), body_style)]
        ]
        
        t = Table(profile_data, colWidths=[150, 380])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (1,0), colors.HexColor('#F4F6F9')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 15))

        # ─── 3. ADVERSE MEDIA FINDINGS ───
        story.append(Paragraph("3. Adverse Media Findings", h1_style))
        articles = case_data.get('articles', [])
        if not articles:
            story.append(Paragraph("No relevant adverse media articles detected.", body_style))
        else:
            for i, art in enumerate(articles, 1):
                story.append(Paragraph(f"<b>{i}. {art.get('title')}</b>", h2_style))
                story.append(Paragraph(f"Source: {art.get('source')} | Credibility: {art.get('credibility_score')}/100 | Tier: {art.get('source_tier')}", body_style))
                story.append(Paragraph(f"Summary: {art.get('summary', 'No summary available.')}", body_style))
                story.append(Spacer(1, 5))
        story.append(Spacer(1, 10))

        # ─── 4. PEP FINDINGS ───
        story.append(Paragraph("4. PEP Findings", h1_style))
        peps = case_data.get('pep_matches', [])
        if not peps:
            story.append(Paragraph("No Politically Exposed Person (PEP) status matches found.", body_style))
        else:
            for pep in peps:
                story.append(Paragraph(f"• <b>{pep.get('entity_name')}</b> - Role: {pep.get('role')} (Country: {pep.get('country')})", bullet_style))
                story.append(Paragraph(f"  Confidence: {pep.get('confidence')*100:.1f}% | {pep.get('justification')}", bullet_style))
        story.append(Spacer(1, 10))

        # ─── 5. SANCTIONS FINDINGS ───
        story.append(Paragraph("5. Sanctions Findings", h1_style))
        sanctions = case_data.get('sanctions_matches', [])
        if not sanctions:
            story.append(Paragraph("No active sanctions listings detected on monitored watchlists.", body_style))
        else:
            for sanc in sanctions:
                story.append(Paragraph(f"• <b>{sanc.get('entity_name')}</b> - Watchlist: {sanc.get('watchlist')}", bullet_style))
                story.append(Paragraph(f"  Confidence: {sanc.get('confidence')*100:.1f}% | {sanc.get('justification')}", bullet_style))
        story.append(Spacer(1, 10))

        # ─── 6. TIMELINE ───
        story.append(Paragraph("6. Chronological Risk Timeline", h1_style))
        timeline_events = case_data.get('events', [])
        if not timeline_events:
            story.append(Paragraph("No events extracted to populate timeline.", body_style))
        else:
            for event in sorted(timeline_events, key=lambda x: x.get('detected_date') or ''):
                story.append(Paragraph(
                    f"<b>{event.get('detected_date', 'N/A')}</b> - [{event.get('event_type')}] (Severity: {event.get('severity')}/100)<br/>"
                    f"Description: {event.get('description')}",
                    body_style
                ))
                story.append(Spacer(1, 4))
        story.append(Spacer(1, 10))

        # ─── 7. NETWORK ANALYSIS ───
        story.append(Paragraph("7. Corporate & Network Analysis", h1_style))
        directors = case_data.get('directors', [])
        shareholders = case_data.get('shareholders', [])
        ubo = case_data.get('beneficial_owners', [])
        subsidiaries = case_data.get('subsidiaries', [])
        
        story.append(Paragraph(f"<b>Ultimate Beneficial Owners (UBOs):</b> {', '.join(ubo) if ubo else 'None identified.'}", body_style))
        story.append(Paragraph(f"<b>Key Directors:</b> {', '.join(directors) if directors else 'None identified.'}", body_style))
        story.append(Paragraph(f"<b>Major Shareholders:</b> {', '.join(shareholders) if shareholders else 'None identified.'}", body_style))
        story.append(Paragraph(f"<b>Subsidiaries:</b> {', '.join(subsidiaries) if subsidiaries else 'None identified.'}", body_style))
        story.append(Spacer(1, 10))

        # ─── 8. RISK SCORING ───
        story.append(Paragraph("8. Risk Scoring Breakdown", h1_style))
        breakdown = case_data.get('risk_breakdown', {})
        score_table_data = [
            [Paragraph("Risk Factor", meta_label_style), Paragraph("Weighted Score (0-100)", meta_label_style)],
            [Paragraph("Overall Combined Risk", body_style), Paragraph(str(breakdown.get('overall', 0)), body_style)],
            [Paragraph("Adverse Media & Fraud Risk", body_style), Paragraph(str(breakdown.get('fraud', 0)), body_style)],
            [Paragraph("Regulatory Enforcement Risk", body_style), Paragraph(str(breakdown.get('regulatory', 0)), body_style)],
            [Paragraph("PEP Exposure", body_style), Paragraph(str(breakdown.get('pep', 0)), body_style)],
            [Paragraph("Sanctions Watchlist Match", body_style), Paragraph(str(breakdown.get('sanctions', 0)), body_style)],
            [Paragraph("Network/Contagion Risk", body_style), Paragraph(str(breakdown.get('network', 0)), body_style)]
        ]
        t_score = Table(score_table_data, colWidths=[250, 280])
        t_score.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (1,0), colors.HexColor('#F4F6F9')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_score)
        story.append(Spacer(1, 15))

        # ─── 9. RECOMMENDATIONS ───
        story.append(Paragraph("9. Recommendations & Compliance Action Plan", h1_style))
        story.append(Paragraph(f"<b>Recommendation:</b> {case_data.get('recommendation', 'REQUIRES_HUMAN_REVIEW')}", h2_style))
        story.append(Paragraph(f"<b>Justification:</b> {case_data.get('recommendation_justification', 'Compliance review required.')}", body_style))
        story.append(Spacer(1, 10))

        # ─── 10. EVIDENCE APPENDIX ───
        story.append(Paragraph("10. Evidence Appendix", h1_style))
        evidence = case_data.get('evidence', [])
        if not evidence:
            story.append(Paragraph("All evidence materials references are logged in Adverse Media & Sanctions sections.", body_style))
        else:
            for item in evidence:
                story.append(Paragraph(f"• {item}", bullet_style))
        story.append(Spacer(1, 10))

        # ─── 11. AUDIT TRAIL ───
        story.append(Paragraph("11. Audit Trail & QA Review Status", h1_style))
        story.append(Paragraph(f"<b>Regulator QA Status:</b> {case_data.get('regulator_qa_status', 'PENDING')}", body_style))
        qa_defs = case_data.get('regulator_qa_deficiencies', [])
        if qa_defs:
            story.append(Paragraph("<b>Deficiencies identified by Regulator QA Agent:</b>", body_style))
            for df in qa_defs:
                story.append(Paragraph(f"- {df}", bullet_style))
        else:
            story.append(Paragraph("Regulator QA Validation: Passed with no compliance deficiencies.", body_style))
            
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Report Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", body_style))

        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
