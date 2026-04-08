"""
Export API
数据导出 API - 支持 Profile 和简历数据导出
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.export_service import export_service
from app.services.pdf_generator import pdf_generator
from app.api.deps import verify_agent_signature


router = APIRouter()


@router.get(
    "/profiles/{profile_id}",
    summary="Export profile as JSON",
    description="Export profile data including agent info and resume data as JSON",
)
async def export_profile_json(
    profile_id: str,
    include_resume: bool = Query(True, description="Include resume data"),
    db: AsyncSession = Depends(get_db),
    agent_id: str = Depends(verify_agent_signature),
):
    """
    Export profile data as JSON.

    - **profile_id**: Profile ID to export
    - **include_resume**: Whether to include resume parsing results
    """
    export_data = await export_service.export_profile_json(
        db=db,
        profile_id=profile_id,
        include_resume=include_resume,
    )

    if not export_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )

    filename = export_service.generate_export_filename(profile_id, "profile")

    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get(
    "/profiles/{profile_id}/pdf",
    summary="Export profile as PDF",
    description="Export profile data as PDF document",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF document",
        },
    },
)
async def export_profile_pdf(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    agent_id: str = Depends(verify_agent_signature),
):
    """
    Export profile data as PDF.

    - **profile_id**: Profile ID to export
    """
    export_data = await export_service.export_profile_json(
        db=db,
        profile_id=profile_id,
        include_resume=True,
    )

    if not export_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )

    pdf_content = pdf_generator.generate_profile_pdf(export_data)
    filename = export_service.generate_export_filename(profile_id, "profile").replace(".json", ".pdf")

    return StreamingResponse(
        iter([pdf_content]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get(
    "/resumes/{resume_id}",
    summary="Export resume as JSON",
    description="Export resume data including parsed content as JSON",
)
async def export_resume_json(
    resume_id: str,
    db: AsyncSession = Depends(get_db),
    agent_id: str = Depends(verify_agent_signature),
):
    """
    Export resume data as JSON.

    - **resume_id**: Resume ID to export
    """
    export_data = await export_service.export_resume_json(
        db=db,
        resume_id=resume_id,
    )

    if not export_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume {resume_id} not found",
        )

    filename = f"agenthire_resume_{resume_id}.json"

    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get(
    "/resumes/{resume_id}/pdf",
    summary="Export resume as PDF",
    description="Export resume data as PDF document",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF document",
        },
    },
)
async def export_resume_pdf(
    resume_id: str,
    db: AsyncSession = Depends(get_db),
    agent_id: str = Depends(verify_agent_signature),
):
    """
    Export resume data as PDF.

    - **resume_id**: Resume ID to export
    """
    export_data = await export_service.export_resume_json(
        db=db,
        resume_id=resume_id,
    )

    if not export_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume {resume_id} not found",
        )

    pdf_content = pdf_generator.generate_resume_pdf(export_data)
    filename = f"agenthire_resume_{resume_id}.pdf"

    return StreamingResponse(
        iter([pdf_content]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get(
    "/history/profiles/{profile_id}",
    summary="Get profile export history",
    description="Get export history for a profile including all resume versions",
)
async def get_export_history(
    profile_id: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of history records"),
    db: AsyncSession = Depends(get_db),
    agent_id: str = Depends(verify_agent_signature),
):
    """
    Get profile export history.

    - **profile_id**: Profile ID
    - **limit**: Maximum number of records to return
    """
    history = await export_service.export_profile_history(
        db=db,
        profile_id=profile_id,
        limit=limit,
    )

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )

    return JSONResponse(content=history)
