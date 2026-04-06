# Profile API

求职者档案管理接口，用于创建、查询、更新求职者 Profile。

---

## 1. 创建 Profile

创建新的求职者档案。

### 端点

```http
POST /api/v1/skill/profiles
```

### 认证方式

无需认证（匿名创建）

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source` | string | 否 | 来源：`manual`(手动) / `resume_parse`(简历解析) |
| `parse_id` | string | 条件 | 当 source=resume_parse 时必填 |
| `profile` | object | 是 | Profile 数据 |
| `agent_metadata` | object | 否 | Agent 元信息 |

### profile 对象

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `basic_info` | object | 是 | 基本信息 |
| `job_intent` | object | 是 | 求职意向 |
| `resume_data` | object | 否 | 完整简历数据 |
| `vector` | array | 否 | 语义向量(384维) |
| `privacy` | object | 否 | 隐私设置 |

### basic_info 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `nickname` | string | 昵称（对外展示） |
| `avatar_url` | string | 头像URL |
| `location` | string | 当前所在地 |

### job_intent 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `target_roles` | array | 目标职位列表 |
| `salary_expectation` | object | 薪资期望 |
| `location_preference` | object | 地点偏好 |
| `skills` | array | 技能列表 |
| `experience_years` | number | 工作年限 |

### privacy 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `contact_encrypted` | string | 加密的联系方式 |
| `public_fields` | array | 公开字段列表 |
| `reveal_on_match` | boolean | 匹配成功后是否公开联系方式 |

### 请求示例

```http
POST /api/v1/skill/profiles
Content-Type: application/json

{
  "source": "resume_parse",
  "parse_id": "parse_abc123",
  "profile": {
    "basic_info": {
      "nickname": "张三",
      "location": "上海"
    },
    "job_intent": {
      "target_roles": ["后端工程师", "架构师"],
      "salary_expectation": {
        "min_monthly": 40000,
        "max_monthly": 60000
      },
      "location_preference": {
        "cities": ["上海", "杭州"],
        "remote_acceptable": true
      },
      "skills": [
        {"name": "Go", "level": "expert", "years": 3},
        {"name": "Kubernetes", "level": "intermediate", "years": 2}
      ],
      "experience_years": 5
    },
    "resume_data": {
      "work_experience": [...],
      "education": [...],
      "skills": [...]
    },
    "vector": [0.1, 0.3, ...],
    "privacy": {
      "contact_encrypted": "base64_encrypted_string",
      "public_fields": ["skills", "experience_years"],
      "reveal_on_match": true
    }
  },
  "agent_metadata": {
    "agent_type": "openclaw",
    "agent_version": "1.0.0",
    "webhook_url": "https://agent.example.com/webhook"
  }
}
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "profile_id": "prof_abc123",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "rt_xyz789",
    "expires_at": "2024-02-15T10:30:00Z",
    "match_subscription_id": "sub_xyz789",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "request_id": "req_abc123"
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `profile_id` | string | Profile ID |
| `access_token` | string | 访问令牌 |
| `refresh_token` | string | 刷新令牌 |
| `expires_at` | string | Token 过期时间 |
| `match_subscription_id` | string | 匹配订阅ID |

---

## 2. 获取 Profile

获取指定 Profile 的详细信息。

### 端点

```http
GET /api/v1/skill/profiles/{profile_id}
```

### 认证方式

JWT Token（只能获取自己的 Profile）

### 请求示例

```http
GET /api/v1/skill/profiles/prof_abc123
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "profile_id": "prof_abc123",
    "status": "active",
    "basic_info": {
      "nickname": "张三",
      "location": "上海"
    },
    "job_intent": {
      "target_roles": ["后端工程师"],
      "salary_expectation": {
        "min_monthly": 40000,
        "max_monthly": 60000
      },
      "skills": [
        {"name": "Go", "level": "expert", "years": 3}
      ]
    },
    "match_stats": {
      "total_matches": 23,
      "new_matches": 5,
      "interested_count": 3
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## 3. 更新 Profile

更新求职者档案信息。

### 端点

```http
PUT /api/v1/skill/profiles/{profile_id}
```

### 认证方式

JWT Token

### 请求参数

与创建 Profile 相同，但所有字段均为可选。

### 请求示例

```http
PUT /api/v1/skill/profiles/prof_abc123
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "profile": {
    "job_intent": {
      "salary_expectation": {
        "min_monthly": 45000,
        "max_monthly": 70000
      }
    }
  }
}
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "profile_id": "prof_abc123",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

---

## 4. 删除 Profile

删除求职者档案（软删除）。

### 端点

```http
DELETE /api/v1/skill/profiles/{profile_id}
```

### 认证方式

JWT Token

### 请求示例

```http
DELETE /api/v1/skill/profiles/prof_abc123
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "profile_id": "prof_abc123",
    "deleted_at": "2024-01-15T11:00:00Z"
  }
}
```

---

## 5. 暂停/恢复匹配

暂停或恢复接收新的匹配推送。

### 端点

```http
POST /api/v1/skill/profiles/{profile_id}/pause
POST /api/v1/skill/profiles/{profile_id}/resume
```

### 认证方式

JWT Token

### 请求示例

```http
POST /api/v1/skill/profiles/prof_abc123/pause
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

{
  "reason": "已找到工作",
  "resume_at": "2024-06-01T00:00:00Z"
}
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "profile_id": "prof_abc123",
    "status": "paused",
    "paused_at": "2024-01-15T11:00:00Z"
  }
}
```

---

## 6. 导出 Profile

导出完整的 Profile 数据（JSON格式）。

### 端点

```http
GET /api/v1/skill/profiles/{profile_id}/export
```

### 认证方式

JWT Token

### 请求示例

```http
GET /api/v1/skill/profiles/prof_abc123/export
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "profile_id": "prof_abc123",
    "export_data": {
      "version": "1.0",
      "exported_at": "2024-01-15T11:00:00Z",
      "profile": { ... },
      "matches_history": [...],
      "resume_files": [...]
    },
    "download_url": "https://storage.agenthire.io/exports/prof_abc123.json?token=xxx"
  }
}
```
