# Matching API

智能匹配接口，用于获取匹配结果和响应匹配。

---

## 1. 获取匹配结果

获取求职者的匹配职位列表。

### 端点

```http
GET /api/v1/skill/matches
```

### 认证方式

JWT Token

### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `profile_id` | string | 是 | Profile ID |
| `status` | string | 否 | 状态筛选：pending/interested/not_interested |
| `limit` | number | 否 | 返回数量，默认10，最大50 |
| `offset` | number | 否 | 偏移量 |

### 请求示例

```http
GET /api/v1/skill/matches?profile_id=prof_abc123&limit=10
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "matches": [
      {
        "match_id": "match_001",
        "job": {
          "job_id": "job_abc",
          "title": "高级后端工程师",
          "company": {
            "name": "XX科技",
            "verified": true,
            "logo_url": "https://..."
          },
          "department": "技术部",
          "salary_range": "35k-50k",
          "location": {
            "city": "上海",
            "remote_policy": "hybrid"
          },
          "requirements": {
            "skills": ["Go", "Kubernetes"],
            "experience_min": 3
          }
        },
        "match_score": 0.89,
        "match_factors": {
          "skill_match": 0.95,
          "experience_match": 0.85,
          "location_match": 1.0,
          "salary_match": 0.90,
          "overall": 0.89
        },
        "status": "pending",
        "created_at": "2024-01-15T10:30:00Z",
        "expires_at": "2024-01-22T10:30:00Z"
      }
    ],
    "total_available": 23,
    "new_matches": 5
  }
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `match_id` | string | 匹配ID |
| `job` | object | 职位信息 |
| `match_score` | float | 匹配分数(0-1) |
| `match_factors` | object | 各维度匹配详情 |
| `status` | string | 匹配状态 |
| `created_at` | string | 匹配创建时间 |
| `expires_at` | string | 匹配过期时间 |

### match_factors 说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `skill_match` | float | 技能匹配度 |
| `experience_match` | float | 经验匹配度 |
| `location_match` | float | 地点匹配度 |
| `salary_match` | float | 薪资匹配度 |
| `overall` | float | 综合得分 |

---

## 2. 响应匹配

对匹配结果表达意向。

### 端点

```http
POST /api/v1/skill/matches/{match_id}/respond
```

### 认证方式

JWT Token

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `response` | string | 是 | 响应类型：`interested` / `not_interested` |
| `message` | string | 否 | 附加消息(最多200字) |

### 请求示例

```http
POST /api/v1/skill/matches/match_001/respond
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "response": "interested",
  "message": "对这个职位很感兴趣，希望能进一步沟通"
}
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "match_id": "match_001",
    "status": "interested",
    "response": {
      "type": "interested",
      "message": "对这个职位很感兴趣...",
      "responded_at": "2024-01-15T11:00:00Z"
    },
    "next_steps": "等待企业方响应"
  }
}
```

---

## 3. 获取匹配详情

获取单个匹配的详细信息。

### 端点

```http
GET /api/v1/skill/matches/{match_id}
```

### 认证方式

JWT Token

### 响应示例

```json
{
  "success": true,
  "data": {
    "match_id": "match_001",
    "profile_id": "prof_abc123",
    "job": {
      "job_id": "job_abc",
      "title": "高级后端工程师",
      "company": { ... },
      "description": "负责微服务架构设计...",
      "requirements": { ... },
      "compensation": { ... },
      "location": { ... }
    },
    "match_score": 0.89,
    "match_factors": { ... },
    "status": "interested",
    "seeker_response": {
      "type": "interested",
      "message": "...",
      "responded_at": "2024-01-15T11:00:00Z"
    },
    "employer_response": null,
    "contact_shared": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

---

## 4. 批量响应匹配

批量对多个匹配进行响应。

### 端点

```http
POST /api/v1/skill/matches/bulk-respond
```

### 认证方式

JWT Token

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `responses` | array | 是 | 响应列表 |

### 请求示例

```http
POST /api/v1/skill/matches/bulk-respond
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "responses": [
    {
      "match_id": "match_001",
      "response": "interested"
    },
    {
      "match_id": "match_002",
      "response": "not_interested"
    }
  ]
}
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "processed": 2,
    "succeeded": 2,
    "failed": 0,
    "results": [
      {
        "match_id": "match_001",
        "status": "success"
      },
      {
        "match_id": "match_002",
        "status": "success"
      }
    ]
  }
}
```

---

## 5. 获取匹配历史

获取历史匹配记录。

### 端点

```http
GET /api/v1/skill/matches/history
```

### 认证方式

JWT Token

### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `profile_id` | string | Profile ID |
| `start_date` | string | 开始日期(YYYY-MM-DD) |
| `end_date` | string | 结束日期(YYYY-MM-DD) |
| `page` | number | 页码 |
| `limit` | number | 每页数量 |

### 响应示例

```json
{
  "success": true,
  "data": {
    "matches": [...],
    "statistics": {
      "total_matches": 45,
      "interested": 12,
      "not_interested": 20,
      "no_response": 13,
      "contact_shared": 3
    },
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45
    }
  }
}
```

---

## 6. 匹配反馈

对匹配结果进行反馈，帮助优化算法。

### 端点

```http
POST /api/v1/skill/matches/{match_id}/feedback
```

### 认证方式

JWT Token

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `score` | number | 是 | 评分(1-5) |
| `reason` | string | 否 | 反馈原因 |
| `outcome` | string | 否 | 最终结果：interview/hired/rejected |

### 请求示例

```http
POST /api/v1/skill/matches/match_001/feedback
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "score": 5,
  "reason": "职位非常符合我的期望",
  "outcome": "interview"
}
```

---

## 匹配状态流转

```
┌─────────┐    ┌─────────────┐    ┌─────────────┐
│ pending │───>│  interested │───>│contact_shared│
└─────────┘    └─────────────┘    └─────────────┘
     │
     ▼
┌─────────────┐
│not_interested│
└─────────────┘
```

| 状态 | 说明 |
|------|------|
| `pending` | 待响应 |
| `interested` | 求职者感兴趣 |
| `not_interested` | 求职者不感兴趣 |
| `contact_shared` | 双方确认，已交换联系方式 |
| `expired` | 已过期 |
