"""
Resume Parsing Service
解析PDF/Word/图片简历，提取结构化信息
"""

import io
from typing import Optional
from PIL import Image

from app.config import get_settings


class ResumeParser:
    """
    Resume parsing service.
    Extracts structured data from resume files using OCR and LLM.
    """

    def __init__(self):
        self.settings = get_settings()
        self._llm_client = None  # Lazy initialization

    @property
    def llm_client(self):
        """Lazy load LLM client."""
        if self._llm_client is None:
            # TODO: Initialize based on settings (OpenAI/Claude)
            self._llm_client = self._create_llm_client()
        return self._llm_client

    def _create_llm_client(self):
        """Create LLM client based on configuration."""
        # Placeholder - will be implemented with actual LLM integration
        return None

    async def parse_resume(
        self,
        file_content: bytes,
        filename: str,
        file_type: str,
        parse_options: Optional[dict] = None,
    ) -> dict:
        """
        Parse resume file and extract structured data.

        Args:
            file_content: Raw file bytes
            filename: Original filename
            file_type: MIME type (pdf, docx, jpg, png)
            parse_options: Optional parsing configuration

        Returns:
            Structured resume data
        """
        parse_options = parse_options or {}

        # Step 1: Extract raw text based on file type
        raw_text = await self._extract_text(file_content, file_type)

        if not raw_text:
            return {
                "success": False,
                "error": "Failed to extract text from file",
            }

        # Step 2: Use LLM to structure the data
        structured_data = await self._extract_structured_data(
            raw_text, parse_options
        )

        # Step 3: Calculate confidence
        confidence = self._calculate_confidence(structured_data)

        # Step 4: Infer job intent
        inferred_intent = self._infer_job_intent(structured_data)

        return {
            "success": True,
            "confidence": confidence,
            "extracted_data": {
                "basic_info": structured_data.get("basic_info", {}),
                "work_experience": structured_data.get("work_experience", []),
                "education": structured_data.get("education", []),
                "skills": structured_data.get("skills", []),
                "projects": structured_data.get("projects", []),
                "self_evaluation": structured_data.get("self_evaluation"),
                "total_work_years": structured_data.get("total_work_years", 0),
                "current_salary": structured_data.get("current_salary"),
                "expected_salary": structured_data.get("expected_salary"),
            },
            "summary": {
                "text": self._generate_summary(structured_data),
                "keywords": structured_data.get("skills", [])[:10],
                "job_intent_inferred": inferred_intent,
            },
            "missing_or_unclear": structured_data.get("missing_fields", []),
            "raw_text_available": True,
        }

    async def _extract_text(self, content: bytes, file_type: str) -> str:
        """
        Extract raw text from file based on type.

        Args:
            content: File bytes
            file_type: MIME type

        Returns:
            Extracted text
        """
        text = ""

        if file_type == "application/pdf":
            text = await self._extract_pdf_text(content)
        elif file_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]:
            text = await self._extract_docx_text(content)
        elif file_type in ["image/jpeg", "image/png", "image/jpg"]:
            text = await self._extract_image_text(content)
        else:
            # Try to decode as text
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1", errors="ignore")

        return text

    async def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from PDF file."""
        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            return "\n".join(text_parts)
        except Exception as e:
            # Fallback: return empty string
            print(f"PDF extraction error: {e}")
            return ""

    async def _extract_docx_text(self, content: bytes) -> str:
        """Extract text from DOCX file."""
        try:
            from docx import Document

            doc = Document(io.BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs]
            return "\n".join(paragraphs)
        except Exception as e:
            print(f"DOCX extraction error: {e}")
            return ""

    async def _extract_image_text(self, content: bytes) -> str:
        """
        Extract text from image using OCR.
        Note: Requires PaddleOCR or similar to be configured.
        """
        try:
            # Try PaddleOCR first
            from paddleocr import PaddleOCR

            ocr = PaddleOCR(use_angle_cls=True, lang="ch")
            result = ocr.ocr(content)

            text_parts = []
            if result:
                for line in result[0]:
                    text_parts.append(line[1][0])

            return "\n".join(text_parts)
        except ImportError:
            # Fallback: use basic OCR or return empty
            print("PaddleOCR not available, using fallback OCR")
            return await self._fallback_ocr(content)
        except Exception as e:
            print(f"OCR extraction error: {e}")
            return ""

    async def _fallback_ocr(self, content: bytes) -> str:
        """Fallback OCR using Pillow."""
        try:
            from PIL import Image
            import pytesseract

            img = Image.open(io.BytesIO(content))
            return pytesseract.image_to_string(img, lang="chi_sim+eng")
        except Exception as e:
            print(f"Fallback OCR error: {e}")
            return ""

    async def _extract_structured_data(
        self, raw_text: str, parse_options: dict
    ) -> dict:
        """
        Use LLM to extract structured data from raw text.

        Args:
            raw_text: Extracted text
            parse_options: Parsing configuration

        Returns:
            Structured data dict
        """
        if not raw_text:
            return {}

        # Truncate text if too long (LLM context limits)
        max_chars = 15000
        truncated_text = raw_text[:max_chars]

        # Build prompt for LLM
        system_prompt = """你是一个专业的简历解析助手。请从简历文本中提取结构化信息。
返回JSON格式，包含以下字段：
- basic_info: 基本信息 {name, phone, email, location, gender, age}
- work_experience: 工作经历 [{company, title, duration, years, description, skills_used, achievements}]
- education: 教育背景 [{school, major, degree, duration}]
- skills: 技能列表 [{name, level, years}]
- projects: 项目经历 [{name, description, technologies}]
- self_evaluation: 自我评价
- current_salary: 当前薪资 {monthly, currency}
- expected_salary: 期望薪资 {min_monthly, max_monthly, currency}
- total_work_years: 总工作年限
- missing_fields: 缺失或不清楚的字段列表

如果某项信息不存在或不确定，返回空值或空列表。"""

        user_prompt = f"请解析以下简历文本：\n\n{truncated_text}"

        try:
            from app.services.llm_client import llm_client

            result = await llm_client.extract_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model="gpt-4o",
                temperature=0.1,
            )

            return result
        except Exception as e:
            print(f"LLM extraction failed: {e}")
            # Fallback to basic extraction
            return {
                "basic_info": {
                    "name": self._extract_name(raw_text),
                    "email": self._extract_email(raw_text),
                    "phone": self._extract_phone(raw_text),
                },
                "work_experience": [],
                "education": [],
                "skills": self._extract_skills_placeholder(raw_text),
                "total_work_years": 0,
                "missing_fields": ["请配置OpenAI API Key以获得完整解析"],
            }

    def _extract_name(self, text: str) -> Optional[str]:
        """Extract name from text (first line usually)."""
        lines = text.strip().split("\n")
        if lines:
            return lines[0].strip()
        return None

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email from text."""
        import re

        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        match = re.search(email_pattern, text)
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text."""
        import re

        # Chinese phone pattern
        phone_pattern = r"1[3-9]\d{9}"
        match = re.search(phone_pattern, text)
        if match:
            return match.group(0)
        return None

    def _extract_skills_placeholder(self, text: str) -> list:
        """Placeholder for skill extraction."""
        # TODO: Implement proper skill extraction
        common_skills = [
            "Python",
            "Java",
            "Go",
            "JavaScript",
            "TypeScript",
            "React",
            "Vue",
            "Node.js",
            "SQL",
            "PostgreSQL",
            "MongoDB",
            "Redis",
            "Docker",
            "Kubernetes",
            "AWS",
            "GCP",
        ]

        found_skills = []
        text_upper = text.upper()
        for skill in common_skills:
            if skill.upper() in text_upper:
                found_skills.append({"name": skill, "level": "unknown"})

        return found_skills

    def _calculate_confidence(self, data: dict) -> float:
        """Calculate parsing confidence score."""
        score = 0.0
        count = 0

        if data.get("basic_info", {}).get("name"):
            score += 0.2
        count += 1

        if data.get("basic_info", {}).get("email"):
            score += 0.2
        count += 1

        if data.get("work_experience"):
            score += 0.3
        count += 1

        if data.get("skills"):
            skill_count = min(len(data["skills"]) / 5, 1.0)
            score += 0.3 * skill_count
        count += 1

        return score if count > 0 else 0.0

    def _infer_job_intent(self, data: dict) -> dict:
        """Infer job search intent from resume data."""
        # TODO: Implement proper intent inference

        latest_job = None
        if data.get("work_experience"):
            latest_job = data["work_experience"][0]

        target_roles = []
        if latest_job:
            target_roles = [latest_job.get("title", "")]

        return {
            "target_roles": target_roles,
            "preferred_industries": [],
            "career_stage": "mid" if data.get("total_work_years", 0) > 3 else "junior",
        }

    def _generate_summary(self, data: dict) -> str:
        """Generate career summary text."""
        years = data.get("total_work_years", 0)
        skills = [s.get("name", "") for s in data.get("skills", [])[:5]]
        latest_job = data.get("work_experience", [{}])[0] if data.get("work_experience") else {}

        parts = [
            f"{years}年经验",
            f"最近职位: {latest_job.get('title', '未知')}",
            f"技能: {','.join(skills) if skills else '未识别'}",
        ]

        return "，".join(filter(None, parts))


# Singleton instance
resume_parser = ResumeParser()


async def parse_resume(
    file_content: bytes,
    filename: str,
    file_type: str,
    parse_options: Optional[dict] = None,
) -> dict:
    """
    Convenience function for resume parsing.

    Args:
        file_content: Raw file bytes
        filename: Original filename
        file_type: MIME type
        parse_options: Optional parsing configuration

    Returns:
        Parsed resume data
    """
    return await resume_parser.parse_resume(
        file_content, filename, file_type, parse_options
    )
