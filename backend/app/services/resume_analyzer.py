"""
简历分析服务
分析简历的优缺点，给出改进建议
"""

from typing import Optional, List, Dict


class ResumeAnalyzer:
    """
    简历分析服务。
    分析简历质量，提供改进建议。
    """

    # 常见缺失字段及建议
    MISSING_FIELD_SUGGESTIONS = {
        "phone": "请提供手机号码，方便企业联系",
        "email": "请提供邮箱地址",
        "location": "请提供所在城市，便于匹配当地职位",
        "total_work_years": "请明确总工作年限，这是筛选条件之一",
        "expected_salary": "请提供期望薪资范围，便于匹配合适岗位",
    }

    # 技能评分标准
    SKILL_LEVELS = {
        "beginner": "初级/入门",
        "intermediate": "中级/熟练",
        "advanced": "高级/精通",
    }

    def __init__(self):
        pass

    async def analyze_resume(
        self,
        resume_data: dict,
        confidence: float,
    ) -> dict:
        """
        分析简历质量并给出改进建议。

        Args:
            resume_data: 解析后的简历数据
            confidence: 解析置信度

        Returns:
            分析报告
        """
        missing_fields = self._check_missing_fields(resume_data)
        strengths = self._identify_strengths(resume_data)
        weaknesses = self._identify_weaknesses(resume_data)
        suggestions = self._generate_suggestions(missing_fields, weaknesses)

        # 质量评分
        quality_score = self._calculate_quality_score(
            resume_data, confidence, strengths, weaknesses
        )

        return {
            "analysis": {
                "quality_score": quality_score,  # 0-100
                "quality_level": self._get_quality_level(quality_score),
                "parse_confidence": confidence,
            },
            "missing_fields": missing_fields,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "suggestions": suggestions,
        }

    def _check_missing_fields(self, resume_data: dict) -> List[dict]:
        """检查缺失或模糊的字段"""
        missing = []

        basic = resume_data.get("basic_info", {})
        if not basic.get("name"):
            missing.append({"field": "name", "suggestion": "请提供姓名"})
        if not basic.get("phone"):
            missing.append({"field": "phone", "suggestion": "请提供手机号码"})
        if not basic.get("email"):
            missing.append({"field": "email", "suggestion": "请提供邮箱地址"})
        if not basic.get("location"):
            missing.append({
                "field": "location",
                "suggestion": "请提供所在城市，便于匹配当地职位"
            })

        # 工作经历检查
        work_exp = resume_data.get("work_experience", [])
        if not work_exp:
            missing.append({
                "field": "work_experience",
                "suggestion": "请补充工作经历，这是招聘方最关注的部分"
            })
        else:
            for i, exp in enumerate(work_exp):
                if not exp.get("company"):
                    missing.append({
                        "field": f"work_experience[{i}].company",
                        "suggestion": f"请补充第{i+1}段工作经历的公司名称"
                    })
                if not exp.get("title"):
                    missing.append({
                        "field": f"work_experience[{i}].title",
                        "suggestion": f"请补充第{i+1}段工作经历的职位"
                    })
                if not exp.get("description"):
                    missing.append({
                        "field": f"work_experience[{i}].description",
                        "suggestion": f"请补充第{i+1}段工作经历的描述"
                    })

        # 技能检查
        skills = resume_data.get("skills", [])
        if not skills:
            missing.append({
                "field": "skills",
                "suggestion": "请补充专业技能，这是匹配算法的关键依据"
            })

        # 教育背景检查
        education = resume_data.get("education", [])
        if not education:
            missing.append({
                "field": "education",
                "suggestion": "请补充教育背景信息"
            })

        return missing

    def _identify_strengths(self, resume_data: dict) -> List[str]:
        """识别简历亮点"""
        strengths = []

        # 工作年限
        years = resume_data.get("total_work_years", 0)
        if years >= 5:
            strengths.append(f"{years}年以上工作经验，具备丰富的实战经验")
        elif years >= 3:
            strengths.append(f"{years}年工作经验，属于中坚力量")

        # 技能数量
        skills = resume_data.get("skills", [])
        if len(skills) >= 10:
            strengths.append(f"掌握{len(skills)}项以上专业技能，技术栈全面")
        elif len(skills) >= 5:
            strengths.append(f"掌握{len(skills)}项专业技能，具备扎实的技术能力")

        # 项目经历
        projects = resume_data.get("projects", [])
        if projects:
            strengths.append(f"有{len(projects)}个重点项目经历")

        # 最近职位
        latest_job = resume_data.get("work_experience", [{}])[0] if resume_data.get("work_experience") else {}
        if latest_job.get("title"):
            strengths.append(f"当前职位：{latest_job['title']}")

        return strengths

    def _identify_weaknesses(self, resume_data: dict) -> List[str]:
        """识别简历问题"""
        weaknesses = []

        # 工作经历描述过于简单
        work_exp = resume_data.get("work_experience", [])
        for exp in work_exp:
            desc = exp.get("description", "")
            if desc and len(desc) < 50:
                weaknesses.append("工作经历描述过于简短，建议补充具体职责和成果")
                break

        # 技能没有等级
        skills = resume_data.get("skills", [])
        for skill in skills:
            if not skill.get("level"):
                weaknesses.append("技能缺少掌握程度（初级/中级/高级），建议补充")
                break

        # 缺少项目经验
        projects = resume_data.get("projects", [])
        if not projects:
            weaknesses.append("建议补充重点项目经历，展示技术实战能力")

        # 缺少自我评价
        if not resume_data.get("self_evaluation"):
            weaknesses.append("建议补充自我评价，让企业更快速了解你的优势")

        return weaknesses

    def _generate_suggestions(
        self,
        missing_fields: List[dict],
        weaknesses: List[str],
    ) -> List[dict]:
        """生成改进建议"""
        suggestions = []

        # 缺失字段的建议
        for field in missing_fields:
            suggestions.append({
                "type": "fill_missing",
                "priority": "high" if field["field"] in ["name", "phone", "email"] else "medium",
                "suggestion": field["suggestion"]
            })

        # 弱点的建议
        for weakness in weaknesses:
            suggestions.append({
                "type": "improve",
                "priority": "medium",
                "suggestion": weakness
            })

        # 优先级排序
        suggestions.sort(key=lambda x: 0 if x["priority"] == "high" else 1)

        return suggestions

    def _calculate_quality_score(
        self,
        resume_data: dict,
        confidence: float,
        strengths: List[str],
        weaknesses: List[str],
    ) -> int:
        """计算简历质量评分（0-100）"""
        score = 50  # 基础分

        # 解析置信度加分（最多 20 分）
        score += confidence * 20

        # 亮点加分（每个亮点 +3 分，最多 +15 分）
        score += min(len(strengths) * 3, 15)

        # 弱点扣分（每个弱点 -3 分，最多 -30 分）
        score -= min(len(weaknesses) * 3, 30)

        # 基础信息完善度加分（最多 +10 分）
        basic = resume_data.get("basic_info", {})
        if basic.get("name") and basic.get("phone") and basic.get("email"):
            score += 10

        return max(0, min(100, score))

    def _get_quality_level(self, score: int) -> str:
        """根据评分获取质量等级"""
        if score >= 80:
            return "优秀"
        elif score >= 60:
            return "良好"
        elif score >= 40:
            return "一般"
        else:
            return "需要改进"


# Singleton instance
resume_analyzer = ResumeAnalyzer()


async def analyze_resume(
    resume_data: dict,
    confidence: float,
) -> dict:
    """
    便捷函数：分析简历。

    Args:
        resume_data: 解析后的简历数据
        confidence: 解析置信度

    Returns:
        分析报告
    """
    return await resume_analyzer.analyze_resume(resume_data, confidence)
