"""
PDF Generator Service
PDF 文档生成服务 - 将 Profile 和简历数据生成为 PDF 格式
"""

import io
from typing import Optional
from datetime import datetime


class PDFGenerator:
    """Service for generating PDF documents from profile/resume data."""

    def generate_profile_pdf(self, profile_data: dict) -> bytes:
        """
        Generate a PDF document from profile data.

        Args:
            profile_data: Profile data dict from export_service

        Returns:
            PDF file content as bytes
        """
        # Simple PDF generation using reportlab or fpdf
        # For now, return a placeholder - can be enhanced with actual PDF library
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.lib.units import inch

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72,
            )

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
            )
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
            )

            story = []

            # Title
            profile = profile_data.get("profile", {})
            nickname = profile.get("nickname", "Unknown")
            story.append(Paragraph(f"Profile Export: {nickname}", title_style))
            story.append(Spacer(1, 0.2 * inch))

            # Export info
            story.append(Paragraph(f"Exported at: {profile_data.get('exported_at', 'N/A')}", body_style))
            story.append(Spacer(1, 0.3 * inch))

            # Basic Info
            story.append(Paragraph("Basic Information", heading_style))
            basic_info = [
                ["Field", "Value"],
                ["Profile ID", profile.get("id", "N/A")],
                ["Status", profile.get("status", "N/A")],
                ["Nickname", profile.get("nickname", "N/A")],
                ["Created At", profile.get("created_at", "N/A")],
                ["Last Active", profile.get("last_active_at", "N/A")],
            ]
            t = Table(basic_info, colWidths=[2 * inch, 4 * inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.3 * inch))

            # Job Intent
            story.append(Paragraph("Job Intent", heading_style))
            job_intent = profile.get("job_intent", {})
            if job_intent:
                story.append(Paragraph(f"Title: {job_intent.get('title', 'N/A')}", body_style))
                story.append(Paragraph(f"Location: {job_intent.get('location', 'N/A')}", body_style))
                story.append(Paragraph(f"Salary Range: {job_intent.get('salary_range', 'N/A')}", body_style))
                skills = job_intent.get("skills", [])
                if skills:
                    story.append(Paragraph(f"Skills: {', '.join(skills)}", body_style))
            else:
                story.append(Paragraph("No job intent data", body_style))
            story.append(Spacer(1, 0.3 * inch))

            # Agent Info
            agent = profile_data.get("agent")
            if agent:
                story.append(Paragraph("Agent Information", heading_style))
                story.append(Paragraph(f"Agent ID: {agent.get('id', 'N/A')}", body_style))
                story.append(Paragraph(f"Name: {agent.get('name', 'N/A')}", body_style))
                story.append(Paragraph(f"Type: {agent.get('type', 'N/A')}", body_style))
                story.append(Paragraph(f"Platform: {agent.get('platform', 'N/A')}", body_style))
                story.append(Spacer(1, 0.3 * inch))

            # Resume Info
            resume = profile_data.get("resume")
            if resume:
                story.append(Paragraph("Resume Information", heading_style))
                story.append(Paragraph(f"Filename: {resume.get('original_filename', 'N/A')}", body_style))
                story.append(Paragraph(f"Parse Status: {resume.get('parse_status', 'N/A')}", body_style))
                story.append(Paragraph(f"Parse Confidence: {resume.get('parse_confidence', 'N/A')}", body_style))

            # Build PDF
            doc.build(story)
            pdf_content = buffer.getvalue()
            buffer.close()
            return pdf_content

        except ImportError:
            # Fallback if reportlab is not installed
            return self._generate_simple_pdf(profile_data)

    def _generate_simple_pdf(self, profile_data: dict) -> bytes:
        """
        Generate a simple text-based PDF when reportlab is not available.

        Args:
            profile_data: Profile data dict

        Returns:
            PDF file content as bytes
        """
        # Simple PDF structure
        profile = profile_data.get("profile", {})
        content = f"""
AgentHire Profile Export
========================

Exported at: {profile_data.get('exported_at', 'N/A')}

Profile Information
-------------------
ID: {profile.get('id', 'N/A')}
Nickname: {profile.get('nickname', 'N/A')}
Status: {profile.get('status', 'N/A')}
Created: {profile.get('created_at', 'N/A')}

Job Intent
----------
{json.dumps(profile.get('job_intent', {}), indent=2)}

Agent: {profile_data.get('agent', {}).get('name', 'N/A')}
        """
        return content.encode('utf-8')

    def generate_resume_pdf(self, resume_data: dict) -> bytes:
        """
        Generate a PDF document from resume data.

        Args:
            resume_data: Resume data dict from export_service

        Returns:
            PDF file content as bytes
        """
        return self._generate_simple_pdf(resume_data)


# Singleton instance
pdf_generator = PDFGenerator()
