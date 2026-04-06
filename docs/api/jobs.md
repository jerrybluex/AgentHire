# Job API

职位发布与管理接口，供企业端调用。

---

## 1. 发布职位

创建新的职位发布。

### 端点

```http
POST /api/v1/skill/jobs
```

### 认证方式

API Key

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `job` | object | 是 | 职位信息 |
| `publish_options` | object | 否 | 发布选项 |

### job 对象

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 职位标题 |
| `department` | string | 否 | 所属部门 |
| `description` | string | 是 | 职位描述 |
| `responsibilities` | array | 否 | 职责列表 |
| `requirements` | object | 是 | 职位要求 |
| `compensation` | object | 否 | 薪酬信息 |
| `location` | object | 否 | 工作地点 |
| `vector` | array | 否 | 语义向量(384维) |

### requirements 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `skills` | array | 技能要求列表 |
| `skill_weights` | object | 技能权重 |
| `experience_min` | number | 最低工作年限 |
| `experience_max` | number | 最高工作年限 |
| `education` | string | 学历要求 |

### compensation 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `salary_min` | number | 最低月薪 |
| `salary_max` | number | 最高月薪 |
| `currency` | string | 货币类型(CNY/USD) |
| `stock_options` | boolean | 是否有期权 |
| `benefits` | array | 福利待遇 |

### location 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `city` | string | 城市 |
| `district` | string | 区县 |
| `address` | string | 详细地址 |
| `remote_policy` | string | 远程政策：onsite/hybrid/remote |

### publish_options 对象

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `active_days` | number | 30 | 职位有效期(天) |
| `auto_match` | boolean | true | 是否自动匹配 |
| `match_threshold` | number | 0.7 | 匹配阈值(0-1) |

### 请求示例

```http
POST /api/v1/skill/jobs
Authorization: Bearer ak_xxxxxxxxxxxxxxxx
Content-Type: application/json

{
  "job": {
    "title": "高级后端工程师",
    "department": "技术部",
    "description": "负责微服务架构设计和核心服务开发",
    "responsibilities": [
      "设计和开发高并发后端服务",
      "优化系统性能和稳定性",
      "指导初中级工程师"
    ],
    "requirements": {
      "skills": ["Go", "微服务", "Kubernetes", "Redis"],
      "skill_weights": {
        "Go": 1.0,
        "微服务": 0.9,
        "Kubernetes": 0.8,
        "Redis": 0.6
      },
      "experience_min": 3,
      "experience_max": 5,
      "education": "本科及以上"
    },
    "compensation": {
      "salary_min": 35000,
      "salary_max": 50000,
      "currency": "CNY",
      "stock_options": true,
      "benefits": ["五险一金", "补充医疗", "带薪年假"]
    },
    "location": {
      "city": "上海",
      "district": "浦东新区",
      "address": "张江高科技园区",
      "remote_policy": "hybrid"
    }
  },
  "publish_options": {
    "active_days": 30,
    "auto_match": true,
    "match_threshold": 0.75
  }
}
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "enterprise_id": "ent_xyz789",
    "status": "active",
    "published_at": "2024-01-15T10:30:00Z",
    "expires_at": "2024-02-14T10:30:00Z",
    "estimated_reach": 150
  }
}
```

---

## 2. 获取职位列表

获取企业发布的职位列表。

### 端点

```http
GET /api/v1/skill/jobs
```

### 认证方式

API Key

### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `status` | string | 状态筛选：active/paused/filled/expired |
| `page` | number | 页码，默认1 |
| `limit` | number | 每页数量，默认20 |

### 响应示例

```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "job_id": "job_abc123",
        "title": "高级后端工程师",
        "status": "active",
        "location": {"city": "上海"},
        "compensation": {"salary_min": 35000, "salary_max": 50000},
        "match_count": 23,
        "published_at": "2024-01-15T10:30:00Z",
        "expires_at": "2024-02-14T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 5,
      "total_pages": 1
    }
  }
}
```

---

## 3. 获取职位详情

获取指定职位的详细信息。

### 端点

```http
GET /api/v1/skill/jobs/{job_id}
```

### 认证方式

API Key

### 响应示例

```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "enterprise_id": "ent_xyz789",
    "title": "高级后端工程师",
    "department": "技术部",
    "description": "负责微服务架构设计...",
    "requirements": { ... },
    "compensation": { ... },
    "location": { ... },
    "status": "active",
    "match_stats": {
      "total_matches": 45,
      "seeker_interested": 12,
      "contact_shared": 5
    },
    "published_at": "2024-01-15T10:30:00Z",
    "expires_at": "2024-02-14T10:30:00Z"
  }
}
```

---

## 4. 更新职位

更新职位信息。

### 端点

```http
PUT /api/v1/skill/jobs/{job_id}
```

### 认证方式

API Key

### 请求参数

与发布职位相同，所有字段可选。

### 请求示例

```http
PUT /api/v1/skill/jobs/job_abc123
Authorization: Bearer ak_xxxxxxxxxxxxxxxx
Content-Type: application/json

{
  "job": {
    "compensation": {
      "salary_max": 55000
    }
  }
}
```

---

## 5. 暂停/恢复职位

暂停或恢复职位发布。

### 端点

```http
POST /api/v1/skill/jobs/{job_id}/pause
POST /api/v1/skill/jobs/{job_id}/resume
```

### 认证方式

API Key

---

## 6. 关闭职位

关闭职位（已招满或停止招聘）。

### 端点

```http
POST /api/v1/skill/jobs/{job_id}/close
```

### 认证方式

API Key

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `reason` | string | 否 | 关闭原因：filled/cancelled/other |

### 请求示例

```http
POST /api/v1/skill/jobs/job_abc123/close
Authorization: Bearer ak_xxxxxxxxxxxxxxxx
Content-Type: application/json

{
  "reason": "filled"
}
```

---

## 7. 获取职位匹配列表

获取指定职位的匹配候选人列表。

### 端点

```http
GET /api/v1/skill/jobs/{job_id}/matches
```

### 认证方式

API Key

### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `status` | string | 状态筛选：pending/interested/not_interested |
| `min_score` | number | 最低匹配分数 |
| `page` | number | 页码 |
| `limit` | number | 每页数量 |

### 响应示例

```json
{
  "success": true,
  "data": {
    "matches": [
      {
        "match_id": "match_001",
        "seeker": {
          "profile_id": "prof_abc",
          "nickname": "张三",
          "skills": ["Go", "Kubernetes"],
          "experience_years": 5
        },
        "match_score": 0.89,
        "match_factors": {
          "skill_match": 0.95,
          "experience_match": 0.85,
          "location_match": 1.0,
          "salary_match": 0.90
        },
        "status": "interested",
        "seeker_message": "对这个职位很感兴趣",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 23
    }
  }
}
```

---

## 8. 响应候选人

对候选人的意向进行响应。

### 端点

```http
POST /api/v1/skill/jobs/{job_id}/matches/{match_id}/respond
```

### 认证方式

API Key

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `response` | string | 是 | 响应：interested/not_interested |
| `message` | string | 否 | 附加消息 |

### 请求示例

```http
POST /api/v1/skill/jobs/job_abc123/matches/match_001/respond
Authorization: Bearer ak_xxxxxxxxxxxxxxxx
Content-Type: application/json

{
  "response": "interested",
  "message": "请发送简历到 hr@company.com"
}
```

---

## 9. 刷新职位

刷新职位，延长有效期并提升曝光。

### 端点

```http
POST /api/v1/skill/jobs/{job_id}/refresh
```

### 认证方式

API Key

### 请求示例

```http
POST /api/v1/skill/jobs/job_abc123/refresh
Authorization: Bearer ak_xxxxxxxxxxxxxxxx
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "expires_at": "2024-03-16T10:30:00Z",
    "refreshed_at": "2024-02-15T10:30:00Z"
  }
}
```
