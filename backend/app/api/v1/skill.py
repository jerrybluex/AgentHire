"""
Skill API endpoints.
Provides resume parsing, intent parsing, and skill-related operations.
"""

from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, status
from pydantic import BaseModel, Field

from app.services.resume_parser import parse_resume
from app.services.intent_parser import parse_seeker_intent, parse_employer_intent

router = APIRouter()


class ParseIntentRequest(BaseModel):
    """Intent parsing request."""

    text: str = Field(..., description="Natural language text to parse")
    type: str = Field(default="seeker", description="Intent type: seeker or employer")
    session_id: str = Field(..., description="Session identifier")


class ParseIntentResponse(BaseModel):
    """Intent parsing response."""

    success: bool = True
    data: dict = Field(default_factory=dict)
    message: str | None = None


class ParseResumeOptions(BaseModel):
    """Options for resume parsing."""

    extract_projects: bool = True
    extract_skills_detail: bool = True
    language_hint: str = "auto"


class ParseResumeResponse(BaseModel):
    """Resume parsing response."""

    success: bool = True
    data: Optional[dict] = None
    message: str | None = None
    error: Optional[str] = None


@router.post(
    "/parse-intent",
    response_model=ParseIntentResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse user intent",
    description="Parse natural language into structured intent",
)
async def parse_intent(request: ParseIntentRequest) -> ParseIntentResponse:
    """
    Parse natural language intent from job seekers or employers.

    - type="seeker": Parse job search intent (e.g., "我想找上海的后端工作，30k以上")
    - type="employer": Parse recruitment intent (e.g., "招3年Go经验，负责微服务架构")
    """
    try:
        if request.type == "seeker":
            result = await parse_seeker_intent(request.text)
        elif request.type == "employer":
            result = await parse_employer_intent(request.text)
        else:
            return ParseIntentResponse(
                success=False,
                data={},
                message=f"Unknown intent type: {request.type}. Use 'seeker' or 'employer'.",
            )

        return ParseIntentResponse(
            success=True,
            data=result,
            message="Intent parsed successfully",
        )

    except Exception as e:
        return ParseIntentResponse(
            success=False,
            data={},
            message=f"Intent parsing failed: {str(e)}",
        )


@router.post(
    "/parse-resume",
    response_model=ParseResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse resume file",
    description="Parse PDF/Word resume into structured data",
)
async def parse_resume_endpoint(
    resume_file: UploadFile = File(..., description="Resume file (PDF, DOCX, JPG, PNG)"),
    extract_projects: bool = Form(True, description="Extract project experience"),
    extract_skills_detail: bool = Form(True, description="Detailed skill extraction"),
    language_hint: str = Form("auto", description="Language hint: zh, en, or auto"),
) -> ParseResumeResponse:
    """
    Parse resume file and extract structured data.

    Supports:
    - PDF files (.pdf)
    - Word documents (.docx)
    - Images (.jpg, .jpeg, .png) with OCR

    Returns:
        Structured resume data including basic info, work experience,
        education, skills, and inferred job intent.
    """
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/jpg",
        "image/png",
    ]

    if resume_file.content_type not in allowed_types:
        return ParseResumeResponse(
            success=False,
            data=None,
            error=f"Unsupported file type: {resume_file.content_type}. Supported: PDF, DOCX, JPG, PNG",
        )

    # Read file content
    file_content = await resume_file.read()

    if len(file_content) == 0:
        return ParseResumeResponse(
            success=False,
            data=None,
            error="Empty file uploaded",
        )

    # Check file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if len(file_content) > max_size:
        return ParseResumeResponse(
            success=False,
            data=None,
            error=f"File too large. Maximum size: 10MB. Got: {len(file_content) / 1024 / 1024:.2f}MB",
        )

    parse_options = {
        "extract_projects": extract_projects,
        "extract_skills_detail": extract_skills_detail,
        "language_hint": language_hint,
    }

    try:
        result = await parse_resume(
            file_content=file_content,
            filename=resume_file.filename or "unknown",
            file_type=resume_file.content_type,
            parse_options=parse_options,
        )

        if result.get("success"):
            return ParseResumeResponse(
                success=True,
                data=result,
                message="Resume parsed successfully",
            )
        else:
            return ParseResumeResponse(
                success=False,
                data=None,
                error=result.get("error", "Unknown parsing error"),
            )

    except Exception as e:
        return ParseResumeResponse(
            success=False,
            data=None,
            error=f"Parsing failed: {str(e)}",
        )
