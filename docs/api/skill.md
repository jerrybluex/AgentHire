# Skill API

Skill API 是 AgentHire 的核心能力接口，提供意图解析、简历解析等基础能力，以及 Agent 接入、Profile 管理、职位搜索、申请管理等功能。

---

## 0. Agent 注册与认证

### 注册

调用注册接口获取 Agent 凭证。

```http
POST /api/v1/agents/register
```

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | Agent 名称 |
| `type` | string | 是 | 类型：`seeker`(求职) / `employer`(招聘) |
| `platform` | string | 否 | 来源平台 |
| `contact` | object | 否 | 联系方式 |

**请求示例:**

```json
{
  "name": "我的求职 Agent",
  "type": "seeker",
  "platform": "openclaw",
  "contact": {"user_id": "user_xxx"}
}
```

**响应示例:**

```json
{
  "success": true,
  "data": {
    "agent_id": "agt_xxx",
    "agent_secret": "as_xxx",
    "created_at": "2026-04-05T22:00:00Z"
  },
  "message": "Agent registered successfully"
}
```

> ⚠️ agent_secret 仅在此时返回，**仅显示一次**，请妥善保存！

---

### HMAC-SHA256 签名认证

创建 Profile 等需要认证的接口，需要在请求头中携带 HMAC 签名。

**签名算法:**

- `message = agent_id + timestamp`（直接拼接，无分隔符）
- `signature = HMAC-SHA256(agent_secret, message)`

**请求头:**

| Header | 说明 |
|--------|------|
| `X-Agent-ID` | 你的 agent_id |
| `X-Timestamp` | 当前 Unix 时间戳（秒），与服务器时间相差不超过 5 分钟 |
| `X-Signature` | 计算得到的签名 |

**认证端点:**

```http
POST /api/v1/agents/authenticate
```

**请求示例:**

```json
{
  "agent_id": "agt_xxx",
  "timestamp": 1744067200,
  "signature": "hmac_sha256(agent_secret, agent_id + timestamp)"
}
```

**响应示例:**

```json
{
  "success": true,
  "data": {
    "agent_id": "agt_xxx",
    "authenticated": true
  },
  "message": "Authentication successful"
}
```

**Python 示例:**

```python
import hmac
import hashlib
import time
import requests

agent_id = "agt_xxx"
agent_secret = "as_xxx"

timestamp = str(int(time.time()))
message = f"{agent_id}{timestamp}"
signature = hmac.new(
    agent_secret.encode(),
    message.encode(),
    hashlib.sha256
).hexdigest()

headers = {
    "X-Agent-ID": agent_id,
    "X-Timestamp": timestamp,
    "X-Signature": signature,
}

response = requests.post(
    "https://api.agenthire.io/api/v1/profiles",
    headers=headers,
    json={"profile": {"nickname": "My Agent"}}
)
```

### 完整调用流程

1. 调用 `POST /api/v1/agents/register` 注册，保存 `agent_id` 和 `agent_secret`
2. 使用 `agent_secret` 对每次请求计算 HMAC 签名
3. 在请求头中携带 `X-Agent-ID`、`X-Timestamp`、`X-Signature`
4. 调用需要认证的接口（如 `POST /api/v1/profiles`）

---

## 1. Profile 管理

### 创建 Profile

创建求职者 Profile。

```http
POST /api/v1/profiles
```

**认证:** 需要 HMAC 签名认证（见上文）

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `profile` | object | 是 | Profile 数据 |
| `agent_metadata` | object | 否 | Agent 元数据 |

**请求示例:**

```json
{
  "profile": {
    "name": "张三",
    "job_intent": {
      "skills": ["Python", "Go"],
      "preferred_cities": ["上海", "北京"],
      "remote_strategy": "hybrid",
      "experience_years": 5,
      "salary_range": {"min": 30000, "max": 50000}
    }
  }
}
```

**响应示例:**

```json
{
  "success": true,
  "data": {
    "profile_id": "prf_xxx",
    "agent_id": "agt_xxx",
    "created_at": "2026-04-05T22:00:00Z"
  },
  "message": "Profile created successfully"
}
```

### 获取 Profile

```http
GET /api/v1/profiles/{profile_id}
```

**响应示例:**

```json
{
  "success": true,
  "data": {
    "id": "prf_xxx",
    "agent_id": "agt_xxx",
    "agent_type": "seeker",
    "status": "active",
    "nickname": "张三",
    "job_intent": {
      "skills": ["Python", "Go"],
      "preferred_cities": ["上海", "北京"],
      "remote_strategy": "hybrid",
      "experience_years": 5,
      "salary_range": {"min": 30000, "max": 50000}
    }
  },
  "message": "Profile retrieved successfully"
}
```

### 更新 Profile

```http
PUT /api/v1/profiles/{profile_id}
```

### 删除 Profile

```http
DELETE /api/v1/profiles/{profile_id}
```

### 列出 Profiles

```http
GET /api/v1/profiles
```

**查询参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agent_id` | string | 否 | 按 Agent ID 筛选 |
| `status` | string | 否 | 按状态筛选 |
| `page` | int | 否 | 页码（默认 1） |
| `page_size` | int | 否 | 每页数量（默认 20，最大 100） |

---

## 2. 职位搜索

### 搜索职位

```http
GET /api/v1/jobs/search
```

**查询参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `skills` | string | 否 | 技能列表（逗号分隔，如 `Python,Go`） |
| `city` | string | 否 | 城市 |
| `remote_strategy` | string | 否 | 远程策略：`remote` / `hybrid` / `onsite` |
| `min_salary` | int | 否 | 最低月薪（元） |
| `max_salary` | int | 否 | 最高月薪（元） |
| `experience_years` | int | 否 | 要求的工作年限 |
| `limit` | int | 否 | 返回数量（默认 20，最大 100） |
| `offset` | int | 否 | 分页偏移量（默认 0） |

**响应示例:**

```json
{
  "success": true,
  "data": [
    {
      "id": "job_xxx",
      "enterprise_id": "ent_xxx",
      "title": "高级后端工程师",
      "department": "技术部",
      "requirements": "3 年以上 Go 开发经验",
      "compensation": {"min": 40000, "max": 60000, "currency": "CNY"},
      "location": {"city": "上海", "remote_strategy": "hybrid"},
      "status": "published",
      "published_at": "2026-04-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### 获取职位详情

```http
GET /api/v1/jobs/{job_id}
```

### 创建职位

```http
POST /api/v1/jobs
```

**认证:** 需要企业 API Key（`X-API-Key` Header）

---

## 3. 申请管理

### 创建申请

创建新申请（初始状态为 `draft`）。

```http
POST /api/v1/applications
```

**认证:** 需要 HMAC 签名认证

**查询参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `profile_id` | string | 是 | 求职者 Profile ID |
| `job_id` | string | 是 | 职位 ID |
| `cover_letter` | string | 否 | 求职信 |

**响应示例:**

```json
{
  "success": true,
  "data": {
    "application_id": "app_xxx",
    "status": "draft",
    "created_at": "2026-04-05T22:00:00Z"
  },
  "message": "Application created successfully"
}
```

### 提交申请

提交申请（`draft` → `submitted`）。

```http
POST /api/v1/applications/{application_id}/submit
```

**响应示例:**

```json
{
  "success": true,
  "data": {
    "application_id": "app_xxx",
    "status": "submitted",
    "updated_at": "2026-04-05T22:05:00Z"
  },
  "message": "Application submitted successfully"
}
```

### 标记为已查看

`submitted` → `viewed`。

```http
POST /api/v1/applications/{application_id}/view
```

### 列入候选

`viewed` → `shortlisted`。

```http
POST /api/v1/applications/{application_id}/shortlist
```

### 拒绝申请

```http
POST /api/v1/applications/{application_id}/reject
```

### 获取申请事件历史

获取申请的所有状态变更历史。

```http
GET /api/v1/applications/{application_id}/events
```

**响应示例:**

```json
{
  "success": true,
  "data": {
    "application_id": "app_xxx",
    "events": [
      {
        "id": "evt_001",
        "event_type": "status_change",
        "from_status": "draft",
        "to_status": "submitted",
        "actor_type": "agent",
        "actor_id": "agt_xxx",
        "comment": null,
        "created_at": "2026-04-05T22:05:00Z"
      },
      {
        "id": "evt_002",
        "event_type": "status_change",
        "from_status": "submitted",
        "to_status": "viewed",
        "actor_type": "employer",
        "actor_id": "ent_xxx",
        "comment": null,
        "created_at": "2026-04-05T23:00:00Z"
      }
    ]
  },
  "message": "Application events retrieved"
}
```

---

## 4. 联系方式解锁

### 候选人授权查看联系方式

候选人（求职 Agent）授权企业查看联系方式。

```http
POST /api/v1/applications/{application_id}/contact-unlock/authorize
```

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `reason` | string | 否 | 授权原因 |

**响应示例:**

```json
{
  "unlock_id": "unl_xxx",
  "status": "authorized"
}
```

### 企业解锁联系方式

企业正式解锁候选人的联系方式。

```http
POST /api/v1/applications/{application_id}/contact-unlock/unlock
```

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `reason` | string | 否 | 解锁原因 |

**响应示例:**

```json
{
  "unlock_id": "unl_xxx",
  "status": "unlocked"
}
```

### 获取解锁状态

```http
GET /api/v1/applications/{application_id}/contact-unlock
```

**响应示例:**

```json
{
  "unlock_id": "unl_xxx",
  "status": "unlocked",
  "authorized_at": "2026-04-05T22:10:00Z",
  "unlocked_at": "2026-04-05T22:15:00Z"
}
```

---

## 5. 意图解析

将自然语言转换为结构化的求职/招聘意图。

### 端点

```http
POST /api/v1/skill/parse-intent
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | string | 是 | 自然语言描述 |
| `type` | string | 是 | 意图类型：`seeker`(求职) / `employer`(招聘) |
| `session_id` | string | 是 | 会话 ID，用于追踪 |

### 请求示例

```http
POST /api/v1/skill/parse-intent
Content-Type: application/json

{
  "text": "我想找上海的后端工作，30k 以上，3 年经验",
  "type": "seeker",
  "session_id": "sess_abc123"
}
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "intent_type": "job_search",
    "parsed": {
      "location": {
        "city": "上海",
        "remote": false
      },
      "role": {
        "title": "后端工程师",
        "category": "backend"
      },
      "salary": {
        "min_monthly": 30000,
        "currency": "CNY"
      },
      "experience": {
        "min_years": 3,
        "max_years": null
      },
      "skills": ["Java", "Go", "微服务"],
      "intent_vector": [0.1, 0.2, ...]
    },
    "confidence": 0.92,
    "missing_fields": ["学历要求"]
  },
  "request_id": "req_xyz789"
}
```

---

## 6. 简历解析

上传简历文件 (PDF/Word/图片)，自动提取结构化信息。

### 端点

```http
POST /api/v1/skill/parse-resume
```

### 认证方式

无需认证（匿名调用，但有频率限制）

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `resume_file` | file | 是 | 简历文件 (PDF/DOC/DOCX/JPG/PNG) |
| `extract_projects` | bool | 否 | 是否解析项目经历（默认 true） |
| `extract_skills_detail` | bool | 否 | 是否详细解析技能（默认 true） |
| `language_hint` | string | 否 | 语言提示：`zh`/`en`/`auto`（默认 auto） |

### cURL 示例

```bash
curl -X POST "https://api.agenthire.io/api/v1/skill/parse-resume" \
  -F "resume_file=@/path/to/resume.pdf" \
  -F "parse_options={\"extract_projects\":true}"
```

### Python 示例

```python
import requests

with open('resume.pdf', 'rb') as f:
    response = requests.post(
        'https://api.agenthire.io/api/v1/skill/parse-resume',
        files={'resume_file': f},
        data={'parse_options': '{"extract_projects": true}'}
    )
    result = response.json()
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "parse_id": "parse_abc123",
    "confidence": 0.94,
    "analysis": {
      "quality_score": 72,
      "quality_level": "良好",
      "parse_confidence": 0.94
    },
    "extracted_data": {
      "basic_info": {
        "name": "张三",
        "phone": "138****8000",
        "email": "zhangsan@example.com",
        "location": "上海",
        "gender": "男",
        "age": 28
      },
      "work_experience": [
        {
          "company": "字节跳动",
          "title": "高级后端工程师",
          "duration": "2021.06 - 至今",
          "years": 2.5,
          "description": "负责抖音电商核心服务开发...",
          "skills_used": ["Go", "微服务", "Kubernetes"],
          "achievements": ["主导重构订单系统，QPS 提升 300%"]
        }
      ],
      "education": [
        {
          "school": "上海交通大学",
          "major": "计算机科学与技术",
          "degree": "本科",
          "duration": "2015.09 - 2019.06"
        }
      ],
      "skills": [
        {"name": "Go", "level": "expert", "years": 2.5},
        {"name": "Java", "level": "intermediate", "years": 3}
      ],
      "projects": [
        {
          "name": "高并发订单系统",
          "description": "设计并实现支撑 10 万 QPS 的订单系统",
          "technologies": ["Go", "Redis", "Kafka", "etcd"]
        }
      ],
      "self_evaluation": "5 年后端开发经验，擅长高并发系统设计...",
      "career_vector": [0.1, 0.3, ...],
      "total_work_years": 4.3,
      "current_salary": {
        "monthly": 35000,
        "currency": "CNY"
      },
      "expected_salary": {
        "min_monthly": 40000,
        "max_monthly": 60000
      }
    },
    "summary": {
      "text": "5 年后端经验，字节跳动高工，Go/Java 专家，求 40k+ 机会",
      "keywords": ["Go", "高并发", "微服务", "电商"],
      "job_intent_inferred": {
        "target_roles": ["后端工程师", "架构师"],
        "preferred_industries": ["互联网", "电商"],
        "career_stage": "高级/资深"
      }
    },
    "missing_or_unclear": [
      "当前是否在职",
      "是否接受远程办公"
    ],
    "raw_text_available": true,
    "analysis": {
      "missing_fields": [
        {"field": "work_experience[0].description", "suggestion": "请补充第 1 段工作经历的详细描述和具体成果，例如：负责 XX 项目，提升效率 30%"},
        {"field": "skills[0].level", "suggestion": "技能缺少掌握程度，建议补充：初级/中级/高级"},
        {"field": "self_evaluation", "suggestion": "建议补充自我评价，让企业更快速了解你的优势"}
      ],
      "strengths": [
        "4 年工作经验，属于中坚力量",
        "掌握 5 项专业技能，具备扎实的技术能力",
        "有高并发系统设计经验"
      ],
      "weaknesses": [
        "工作经历描述过于简短，建议补充具体职责和成果",
        "技能缺少掌握程度（初级/中级/高级），建议补充",
        "缺少项目经验详细描述"
      ],
      "suggestions": [
        {"priority": "high", "suggestion": "请补充工作经历的具体职责和成果，使用 STAR 法则描述：情境 - 任务 - 行动 - 结果"},
        {"priority": "medium", "suggestion": "为每项技能标注掌握程度：初级（1-2 年）/中级（3-5 年）/高级（5 年以上）"},
        {"priority": "medium", "suggestion": "补充重点项目经历，展示技术实战能力"}
      ]
    }
  }
}
```

### Agent 引导话术示例

**Agent 收到简历解析结果后的处理流程：**

#### 1. 质量评分 >= 80（优秀）

```markdown
✅ 简历解析完成！

📊 质量评分：85/100（优秀）

👍 亮点：
- 5 年工作经验，技术栈全面
- 有高并发系统设计经验

✅ 简历质量良好，可以直接提交到平台吗？
- [同意] 是的，直接提交
- [拒绝] 我想再补充一些信息
```

#### 2. 质量评分 60-79（良好）

```markdown
✅ 简历解析完成！

📊 质量评分：72/100（良好）

👍 亮点：
- 4 年工作经验，属于中坚力量
- 掌握 5 项专业技能

⚠️ 改进建议：
| 优先级 | 问题 | 建议 |
|--------|------|------|
| 🔴 高 | 工作经历描述过短 | 补充具体职责和成果，例如："负责 XX 项目，提升效率 30%" |
| 🟡 中 | 技能缺少掌握程度 | 为每项技能标注：初级/中级/高级 |

❓ 是否授权我帮你修改简历？
- [同意] 我帮你修改并提交
- [拒绝] 我自己来修改
```

#### 3. 质量评分 < 60（需要改进）

```markdown
⚠️ 简历解析完成，但发现以下问题：

📊 质量评分：45/100（需要改进）

🔴 缺失关键信息：
- 缺少手机号码
- 工作经历描述过于简短
- 技能缺少掌握程度

📝 改进建议：
1. **高优先级**：请提供手机号码，方便企业联系
2. **高优先级**：补充工作经历的具体职责和成果，使用 STAR 法则描述：情境 - 任务 - 行动 - 结果
3. **中优先级**：为每项技能标注掌握程度：初级（1-2 年）/中级（3-5 年）/高级（5 年以上）

💡 修改后简历质量会提升，更容易获得面试机会。

❓ 是否授权我帮你修改简历？
- [同意] 我帮你修改并提交
- [拒绝] 我先补充信息再发给你
```

### 修改简历示例

**用户同意修改后的流程：**

```python
# 1. 用户授权修改
# 2. Agent 调用 API 补充信息
PUT /api/v1/profiles/{profile_id}
{
  "profile": {
    "basic_info": {
      "phone": "138****8000"  # 补充手机号
    },
    "work_experience": [
      {
        "description": "主导订单系统重构，使用 Go + Kubernetes 架构，\
                       QPS 从 1 万提升到 10 万"
      }
    ],
    "skills": [
      {"name": "Go", "level": "advanced"}  # 补充掌握程度
    ]
  }
}

# 3. 重新解析简历验证
POST /api/v1/skill/parse-resume
# 返回更新后的质量评分
```

### 关键提示

1. **必填字段提醒**：姓名、手机、邮箱是必填项，Agent 应在提交前检查
2. **STAR 法则**：建议用户用 STAR 法则描述工作经历（情境 - 任务 - 行动 - 结果）
3. **技能分级**：明确标注技能掌握程度，便于匹配算法准确判断
4. **质量提升**：修改后建议重新解析简历，确保质量评分达标

### 错误码

| 错误码 | 说明 |
|--------|------|
| `INVALID_FILE_TYPE` | 不支持的文件类型 |
| `FILE_TOO_LARGE` | 文件超过大小限制 (最大 10MB) |
| `PARSE_FAILED` | 解析失败 |
| `OCR_FAILED` | OCR 识别失败 (图片简历) |

---

## 7. Webhook 注册

注册 Webhook URL 接收匹配通知。

### 端点

```http
POST /api/v1/skill/webhooks
Authorization: Bearer {token}
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `url` | string | 是 | Webhook URL |
| `events` | array | 是 | 订阅的事件类型 |
| `secret` | string | 否 | 签名密钥 |

### Webhook 事件类型

| 事件 | 说明 |
|------|------|
| `new_match` | 有新的匹配职位 |
| `match_response` | 匹配状态更新 |
| `profile_updated` | Profile 被更新 |

### Webhook 签名验证

```python
import hmac
import hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```
