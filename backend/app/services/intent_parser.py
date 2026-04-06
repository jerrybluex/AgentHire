"""
Intent Parsing Service
解析自然语言求职/招聘意图
"""

from typing import Optional
from app.services.llm_client import llm_client


class IntentParser:
    """
    Job search intent parser.
    Parses natural language into structured job search or recruitment intent.
    """

    async def parse_seeker_intent(self, text: str) -> dict:
        """
        Parse job seeker's natural language intent.

        Args:
            text: Natural language description, e.g.
                  "我想找上海的后端工作，30k以上，3年经验"

        Returns:
            Structured intent with parsed fields
        """
        if not text:
            return self._empty_intent()

        system_prompt = """你是一个求职意图解析助手。请从用户的自然语言描述中提取结构化求职信息。

返回JSON格式，包含以下字段：
- intent_type: "job_search"
- location: 期望工作地点 {city: string, district: optional, remote: boolean}
- role: 目标职位 {title: string, category: string}
- salary: 薪资要求 {min_monthly: number, max_monthly: optional, currency: "CNY"}
- experience: 经验要求 {min_years: number, max_years: optional}
- skills: 技能要求 [string array]
- education: 学历要求 {level: string, optional}
- industry: 期望行业 [string array]
- job_type: 工作类型 (full-time, part-time, contract, intern)
- urgency: 求职紧迫度 (active, passive, urgent)
- confidence: 解析置信度 (0-1)
- missing_fields: 未明确说明的字段列表"""

        try:
            result = await llm_client.extract_json(
                prompt=f"解析以下求职意图：\n{text}",
                system_prompt=system_prompt,
                model="gpt-4o",
                temperature=0.1,
            )

            return result

        except Exception as e:
            print(f"Intent parsing error: {e}")
            return self._empty_intent()

    async def parse_employer_intent(self, text: str) -> dict:
        """
        Parse employer's recruitment intent.

        Args:
            text: Natural language description, e.g.
                  "招3年Go经验，负责微服务架构"

        Returns:
            Structured recruitment intent
        """
        if not text:
            return self._empty_employer_intent()

        system_prompt = """你是一个招聘意图解析助手。请从用户的自然语言描述中提取结构化招聘信息。

返回JSON格式，包含以下字段：
- intent_type: "job_posting"
- title: 职位名称
- department: 部门
- description: 职位描述
- requirements: 任职要求 {
    skills: [string array],
    experience_min: number,
    experience_max: optional,
    education: string,
    language: optional
  }
- compensation: 薪酬待遇 {
    salary_min: number,
    salary_max: number,
    currency: "CNY",
    stock_options: boolean,
    benefits: [string array] optional
  }
- location: 工作地点 {city: string, district: optional, address: optional, remote_policy: "onsite/hybrid/remote"}
- headcount: 招聘人数
- urgency: 招聘紧迫度 (high, normal, low)
- target_candidates: 目标候选人画像 optional
- confidence: 解析置信度 (0-1)
- missing_fields: 未明确说明的字段列表"""

        try:
            result = await llm_client.extract_json(
                prompt=f"解析以下招聘需求：\n{text}",
                system_prompt=system_prompt,
                model="gpt-4o",
                temperature=0.1,
            )

            return result

        except Exception as e:
            print(f"Intent parsing error: {e}")
            return self._empty_employer_intent()

    def _empty_intent(self) -> dict:
        """Return empty seeker intent structure."""
        return {
            "intent_type": "job_search",
            "location": {"city": None, "remote": False},
            "role": {"title": None, "category": None},
            "salary": {"min_monthly": None, "currency": "CNY"},
            "experience": {"min_years": None},
            "skills": [],
            "education": None,
            "industry": [],
            "job_type": "full-time",
            "urgency": "passive",
            "confidence": 0.0,
            "missing_fields": ["请提供更详细的求职意向"],
        }

    def _empty_employer_intent(self) -> dict:
        """Return empty employer intent structure."""
        return {
            "intent_type": "job_posting",
            "title": None,
            "department": None,
            "description": None,
            "requirements": {
                "skills": [],
                "experience_min": None,
                "education": None,
            },
            "compensation": {
                "salary_min": None,
                "salary_max": None,
                "currency": "CNY",
                "stock_options": False,
            },
            "location": {"city": None, "remote_policy": "onsite"},
            "headcount": 1,
            "urgency": "normal",
            "confidence": 0.0,
            "missing_fields": ["请提供更详细的招聘需求"],
        }


# Singleton instance
intent_parser = IntentParser()


async def parse_seeker_intent(text: str) -> dict:
    """Convenience function for parsing seeker intent."""
    return await intent_parser.parse_seeker_intent(text)


async def parse_employer_intent(text: str) -> dict:
    """Convenience function for parsing employer intent."""
    return await intent_parser.parse_employer_intent(text)
