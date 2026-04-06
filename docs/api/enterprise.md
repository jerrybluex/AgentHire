# Enterprise API

企业认证与B端管理接口。

---

## 1. 企业认证申请

提交企业认证申请。

### 端点

```http
POST /api/v1/enterprise/apply
```

### 认证方式

无需认证

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `company_name` | string | 是 | 公司全称 |
| `unified_social_credit_code` | string | 是 | 统一社会信用代码 |
| `business_license` | file | 是 | 营业执照扫描件 |
| `legal_person_id` | file | 是 | 法人身份证 |
| `authorization_letter` | file | 是 | 授权书 |
| `contact` | object | 是 | 联系人信息 |
| `company_website` | string | 否 | 公司官网 |
| `company_size` | string | 否 | 公司规模 |
| `industry` | string | 否 | 所属行业 |

### contact 对象

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 联系人姓名 |
| `phone` | string | 是 | 联系人电话 |
| `email` | string | 是 | 联系人邮箱 |

### 请求示例

```http
POST /api/v1/enterprise/apply
Content-Type: multipart/form-data

--boundary
Content-Disposition: form-data; name="company_name"

XX科技有限公司
--boundary
Content-Disposition: form-data; name="unified_social_credit_code"

91310000XXXXXXXXXX
--boundary
Content-Disposition: form-data; name="business_license"; filename="license.pdf"
Content-Type: application/pdf

<binary data>
--boundary
Content-Disposition: form-data; name="contact"

{"name": "张三", "phone": "13800138000", "email": "hr@example.com"}
--boundary--
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "application_id": "app_abc123",
    "enterprise_id": "ent_xyz789",
    "status": "pending",
    "submitted_at": "2024-01-15T10:30:00Z",
    "estimated_review_time": "1-3个工作日"
  }
}
```

---

## 2. 查询认证状态

查询企业认证申请状态。

### 端点

```http
GET /api/v1/enterprise/applications/{application_id}
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "application_id": "app_abc123",
    "enterprise_id": "ent_xyz789",
    "company_name": "XX科技有限公司",
    "status": "approved",
    "submitted_at": "2024-01-15T10:30:00Z",
    "reviewed_at": "2024-01-16T14:00:00Z",
    "reviewer_note": "认证通过"
  }
}
```

### 状态说明

| 状态 | 说明 |
|------|------|
| `pending` | 审核中 |
| `approved` | 已通过 |
| `rejected` | 已拒绝 |
| `supplement_needed` | 需要补充材料 |

---

## 3. 获取企业信息

获取企业详细信息。

### 端点

```http
GET /api/v1/enterprise/info
```

### 认证方式

Enterprise Token

### 响应示例

```json
{
  "success": true,
  "data": {
    "enterprise_id": "ent_xyz789",
    "name": "XX科技有限公司",
    "unified_social_credit_code": "91310000XXXXXXXXXX",
    "status": "approved",
    "contact": {
      "name": "张三",
      "phone": "13800138000",
      "email": "hr@example.com"
    },
    "website": "https://example.com",
    "industry": "互联网",
    "company_size": "100-500",
    "verified_at": "2024-01-16T14:00:00Z",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## 4. 创建 API Key

创建新的 API Key。

### 端点

```http
POST /api/v1/enterprise/api-keys
```

### 认证方式

Enterprise Token

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | Key 名称 |
| `plan` | string | 否 | 套餐：pay_as_you_go/monthly_basic/monthly_pro |
| `rate_limit` | number | 否 | 每分钟请求限制，默认100 |
| `ip_whitelist` | array | 否 | IP 白名单 |

### 请求示例

```http
POST /api/v1/enterprise/api-keys
Authorization: Bearer {enterprise_token}
Content-Type: application/json

{
  "name": "生产环境Key",
  "plan": "monthly_basic",
  "rate_limit": 1000,
  "ip_whitelist": ["192.168.1.1", "10.0.0.0/8"]
}
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "key_id": "key_abc123",
    "name": "生产环境Key",
    "api_key": "ak_live_xxxxxxxxxxxxxxxx",
    "api_key_prefix": "ak_live",
    "plan": "monthly_basic",
    "rate_limit": 1000,
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z",
    "warning": "请立即保存 API Key，它只显示一次"
  }
}
```

---

## 5. 获取 API Key 列表

获取企业的 API Key 列表。

### 端点

```http
GET /api/v1/enterprise/api-keys
```

### 认证方式

Enterprise Token

### 响应示例

```json
{
  "success": true,
  "data": {
    "api_keys": [
      {
        "key_id": "key_abc123",
        "name": "生产环境Key",
        "api_key_prefix": "ak_live",
        "plan": "monthly_basic",
        "rate_limit": 1000,
        "status": "active",
        "last_used_at": "2024-01-15T11:00:00Z",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

---

## 6. 撤销 API Key

撤销指定的 API Key。

### 端点

```http
DELETE /api/v1/enterprise/api-keys/{key_id}
```

### 认证方式

Enterprise Token

### 响应示例

```json
{
  "success": true,
  "data": {
    "key_id": "key_abc123",
    "revoked_at": "2024-01-15T12:00:00Z"
  }
}
```

---

## 7. 获取账单

获取企业账单记录。

### 端点

```http
GET /api/v1/enterprise/billing
```

### 认证方式

Enterprise Token

### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `start_date` | string | 开始日期(YYYY-MM-DD) |
| `end_date` | string | 结束日期(YYYY-MM-DD) |
| `billing_period` | string | 账单周期(YYYY-MM) |

### 响应示例

```json
{
  "success": true,
  "data": {
    "billing_records": [
      {
        "record_id": "bill_001",
        "usage_type": "job_post",
        "quantity": 5,
        "unit_price": 10.00,
        "amount": 50.00,
        "reference_id": "job_abc123",
        "created_at": "2024-01-15T10:30:00Z"
      },
      {
        "record_id": "bill_002",
        "usage_type": "match_success",
        "quantity": 3,
        "unit_price": 50.00,
        "amount": 150.00,
        "reference_id": "match_001",
        "created_at": "2024-01-15T11:00:00Z"
      }
    ],
    "summary": {
      "total_amount": 200.00,
      "job_post_count": 5,
      "match_query_count": 45,
      "match_success_count": 3
    }
  }
}
```

### 计费项说明

| 计费项 | 单价 | 说明 |
|--------|------|------|
| `job_post` | ¥10/次 | 发布职位 |
| `match_query` | ¥0.5/次 | 查询匹配结果 |
| `match_success` | ¥50/次 | 成功匹配（双向确认） |
| `profile_view` | ¥2/次 | 查看详细候选人信息 |

---

## 8. 获取使用量统计

获取 API 使用量统计。

### 端点

```http
GET /api/v1/enterprise/usage
```

### 认证方式

Enterprise Token

### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `start_date` | string | 开始日期 |
| `end_date` | string | 结束日期 |
| `group_by` | string | 分组方式：day/week/month |

### 响应示例

```json
{
  "success": true,
  "data": {
    "usage_stats": [
      {
        "date": "2024-01-15",
        "job_post": 5,
        "match_query": 45,
        "match_success": 3,
        "profile_view": 12
      }
    ],
    "total": {
      "job_post": 5,
      "match_query": 45,
      "match_success": 3,
      "profile_view": 12
    }
  }
}
```

---

## 套餐说明

| 套餐 | 价格 | 包含 |
|------|------|------|
| 按量付费 | 无月费 | 按实际使用量计费 |
| 基础包月 | ¥999/月 | 包含2000次调用 |
| 专业包月 | ¥2999/月 | 包含10000次调用 + 优先匹配 |
| 企业定制 | 面议 | 专属支持 + 定制功能 |

---

## 更新企业信息

更新企业联系信息等。

### 端点

```http
PUT /api/v1/enterprise/info
```

### 认证方式

Enterprise Token

### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `contact` | object | 联系人信息 |
| `website` | string | 公司官网 |
| `company_size` | string | 公司规模 |
| `industry` | string | 所属行业 |

### 请求示例

```http
PUT /api/v1/enterprise/info
Authorization: Bearer {enterprise_token}
Content-Type: application/json

{
  "contact": {
    "name": "李四",
    "phone": "13900139000",
    "email": "newhr@example.com"
  }
}
```
