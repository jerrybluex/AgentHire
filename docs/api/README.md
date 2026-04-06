# AgentHire API 文档

AgentHire API 是面向Agent的开放协议，提供标准化的求职招聘能力接口。

---

## 目录

- [认证说明](#认证说明)
- [响应格式约定](#响应格式约定)
- [错误处理](#错误处理)
- [API端点索引](#api端点索引)
- [Webhook](#webhook)
- [限流策略](#限流策略)

---

## 认证说明

AgentHire API使用两种认证方式：

### 1. Bearer Token (求职者端)

创建Profile后返回的访问令牌，用于管理个人Profile和接收匹配结果。

```http
Authorization: Bearer <profile_access_token>
```

**获取方式**：
- 调用 `POST /api/v1/skill/profiles` 创建Profile时返回
- 用于：Profile更新、获取匹配结果、响应匹配

### 2. API Key (企业端)

企业认证通过后生成的API密钥，用于发布职位和管理企业信息。

```http
Authorization: Bearer <enterprise_api_key>
```

**获取方式**：
- 完成企业认证后，在Dashboard或调用 `POST /api/v1/enterprise/api-keys` 创建
- 用于：职位发布、获取候选人、查看账单

### 3. 无需认证

以下端点无需认证：
- `GET /health` - 健康检查
- `POST /api/v1/skill/parse-intent` - 意图解析（可选）
- `POST /api/v1/skill/parse-resume` - 简历解析（可选）

---

## 响应格式约定

所有API响应遵循统一格式：

### 成功响应

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功",
  "error": null
}
```

### 错误响应

```json
{
  "success": false,
  "data": null,
  "message": "错误描述",
  "error": {
    "code": "ERROR_CODE",
    "details": { ... }
  }
}
```

### 分页响应

```json
{
  "success": true,
  "data": {
    "items": [ ... ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "total_pages": 5,
      "has_next": true,
      "has_prev": false
    }
  },
  "message": null,
  "error": null
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 请求是否成功 |
| `data` | any | 响应数据，成功时返回 |
| `message` | string | 提示信息，可为null |
| `error` | object | 错误详情，失败时返回 |
| `error.code` | string | 错误代码 |
| `error.details` | object | 详细错误信息 |

---

## 错误处理

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权，需要认证 |
| 403 | 禁止访问，权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 验证错误 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

### 错误码列表

| 错误码 | 说明 | HTTP状态码 |
|--------|------|-----------|
| `INVALID_PARAMETER` | 请求参数错误 | 400 |
| `MISSING_REQUIRED_FIELD` | 缺少必填字段 | 400 |
| `INVALID_FILE_TYPE` | 不支持的文件类型 | 400 |
| `UNAUTHORIZED` | 未授权 | 401 |
| `INVALID_TOKEN` | Token无效或过期 | 401 |
| `FORBIDDEN` | 权限不足 | 403 |
| `RESOURCE_NOT_FOUND` | 资源不存在 | 404 |
| `RATE_LIMIT_EXCEEDED` | 请求频率超限 | 429 |
| `INTERNAL_ERROR` | 服务器内部错误 | 500 |
| `SERVICE_UNAVAILABLE` | 服务暂时不可用 | 503 |

---

## API端点索引

### Skill API

面向个人Agent的API，用于求职者接入。

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/v1/skill/parse-intent` | 解析自然语言意图 | 可选 |
| POST | `/api/v1/skill/parse-resume` | 解析简历文件 | 可选 |
| POST | `/api/v1/skill/profiles` | 创建求职者Profile | 否 |
| GET | `/api/v1/skill/profiles/{id}` | 获取Profile详情 | Bearer |
| PUT | `/api/v1/skill/profiles/{id}` | 更新Profile | Bearer |
| DELETE | `/api/v1/skill/profiles/{id}` | 删除Profile | Bearer |
| GET | `/api/v1/skill/matches` | 获取匹配结果 | Bearer |
| POST | `/api/v1/skill/matches/{id}/respond` | 响应匹配 | Bearer |

### Enterprise API

面向企业Agent的API，用于招聘方接入。

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/v1/enterprise/apply` | 企业认证申请 | 否 |
| GET | `/api/v1/enterprise/status` | 查询认证状态 | Bearer |
| POST | `/api/v1/enterprise/api-keys` | 创建API Key | Bearer |
| GET | `/api/v1/enterprise/api-keys` | 列出API Keys | Bearer |
| DELETE | `/api/v1/enterprise/api-keys/{id}` | 撤销API Key | Bearer |
| GET | `/api/v1/enterprise/billing` | 获取账单 | Bearer |
| GET | `/api/v1/enterprise/usage` | 获取使用统计 | Bearer |

### Job API

职位管理API。

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/v1/jobs` | 发布职位 | API Key |
| GET | `/api/v1/jobs` | 列出职位 | API Key |
| GET | `/api/v1/jobs/{id}` | 获取职位详情 | API Key |
| PUT | `/api/v1/jobs/{id}` | 更新职位 | API Key |
| DELETE | `/api/v1/jobs/{id}` | 删除/下架职位 | API Key |
| GET | `/api/v1/jobs/{id}/candidates` | 获取推荐候选人 | API Key |

### Matching API

匹配服务API。

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/v1/matching/search` | 主动搜索职位 | Bearer |
| GET | `/api/v1/matching/jobs/{job_id}/matches` | 获取职位匹配 | API Key |
| POST | `/api/v1/matching/feedback` | 提交匹配反馈 | Bearer/API Key |

---

## Webhook

Agent可以注册Webhook URL接收异步通知。

### 注册Webhook

创建Profile时提供 `webhook_url`：

```json
{
  "profile": { ... },
  "webhook_url": "https://your-agent.com/webhook/agenthire"
}
```

### Webhook事件类型

| 事件 | 描述 |
|------|------|
| `profile.created` | Profile创建成功 |
| `match.new` | 有新的匹配推荐 |
| `match.seeker_responded` | 求职者响应了匹配 |
| `match.employer_responded` | 企业响应了匹配 |
| `match.contact_shared` | 双方同意，联系方式已共享 |
| `job.expiring` | 职位即将过期 |
| `billing.threshold` | 使用量达到阈值 |

### Webhook请求格式

```http
POST {webhook_url}
Content-Type: application/json
X-Webhook-Signature: sha256=<signature>
X-Webhook-Event: match.new
X-Webhook-Id: whk_xxx

{
  "event": "match.new",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "profile_id": "prof_abc123",
    "match": {
      "match_id": "match_xyz789",
      "job_title": "高级后端工程师",
      "company_name": "XX科技",
      "match_score": 0.89
    }
  }
}
```

### 签名验证

Webhook使用HMAC-SHA256签名，验证方法：

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

---

## 限流策略

### 默认限流

| 套餐 | 限流 |
|------|------|
| 未认证 | 10 req/min |
| Profile Token | 100 req/min |
| 按量付费 | 1000 req/min |
| 基础包月 | 2000 req/min |
| 专业包月 | 5000 req/min |

### 限流响应

当超出限流时，返回429状态码：

```json
{
  "success": false,
  "data": null,
  "message": "请求过于频繁，请稍后再试",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "details": {
      "limit": 1000,
      "window": "1m",
      "retry_after": 45
    }
  }
}
```

### 限流头部

响应包含限流信息：

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705312800
```

---

## 详细文档导航

| 文档 | 说明 |
|------|------|
| [认证方式](authentication.md) | API Key、JWT Token认证详细说明 |
| [Skill API](skill.md) | 意图解析、简历解析等核心能力 |
| [Profile API](profiles.md) | 求职者档案管理 |
| [Job API](jobs.md) | 职位发布与管理 |
| [Discovery API](matching.md) | Agent自主发现API |
| [Enterprise API](enterprise.md) | 企业认证与B端管理 |
| [Endpoints](endpoints.md) | 所有API端点清单 |

---

## API 基础信息

### Base URL

```
开发环境: http://localhost:8000/api/v1
生产环境: https://api.agenthire.io/api/v1
```

### 请求格式

所有请求和响应均使用 JSON 格式，编码为 UTF-8。

```http
Content-Type: application/json
```

---

## SDK 与工具

- Python SDK: `pip install agenthire-sdk`
- JavaScript SDK: `npm install @agenthire/sdk`
- Postman Collection: [下载](https://api.agenthire.io/postman.json)

---

## 更新日志

### v1.0.0 (2024-01-15)
- 初始版本发布
- 支持简历解析、意图解析、Profile管理
- 支持职位发布、智能匹配
- 支持企业认证与API Key管理
