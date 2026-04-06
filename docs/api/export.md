# Export API - 数据导出

数据导出 API 支持将 Profile 和简历数据导出为 JSON 或 PDF 格式。

---

## 目录

- [Profile 导出](#profile-导出)
- [简历导出](#简历导出)
- [导出历史](#导出历史)

---

## Profile 导出

### 导出为 JSON

获取 Profile 的完整数据，包括关联的 Agent 信息和简历信息。

```
GET /api/v1/export/profiles/{profile_id}
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| profile_id | string | 是 | Profile ID |
| include_resume | boolean | 否 | 是否包含简历数据，默认 true |

**响应示例：**

```json
{
  "exported_at": "2026-04-02T10:30:00Z",
  "profile": {
    "id": "prof_abc123",
    "nickname": "张三",
    "avatar_url": "https://...",
    "status": "active",
    "job_intent": {
      "target_roles": ["后端工程师"],
      "salary_expectation": {"min_monthly": 30000, "max_monthly": 50000}
    },
    "privacy": {},
    "match_preferences": {}
  },
  "agent": {
    "id": "agt_xxx",
    "name": "OpenClaw Agent",
    "type": "seeker",
    "platform": "openclaw"
  },
  "resume": {
    "id": "res_yyy",
    "original_filename": "resume.pdf",
    "parse_status": "success",
    "parse_result": {...}
  }
}
```

### 导出为 PDF

导出 Profile 数据为 PDF 文档格式。

```
GET /api/v1/export/profiles/{profile_id}/pdf
```

**响应：** PDF 文件二进制流

---

## 简历导出

### 导出为 JSON

获取简历的完整解析数据。

```
GET /api/v1/export/resumes/{resume_id}
```

**响应示例：**

```json
{
  "exported_at": "2026-04-02T10:30:00Z",
  "resume": {
    "id": "res_yyy",
    "original_filename": "resume.pdf",
    "file_size": 1024,
    "file_type": "pdf",
    "parse_status": "success",
    "parse_result": {
      "name": "张三",
      "skills": ["Python", "Go"],
      "experience": [...]
    }
  },
  "profile": {
    "id": "prof_abc123",
    "nickname": "张三",
    "job_intent": {...}
  }
}
```

### 导出为 PDF

导出简历数据为 PDF 文档格式。

```
GET /api/v1/export/resumes/{resume_id}/pdf
```

---

## 导出历史

获取 Profile 的导出历史记录，包括所有版本的简历信息。

```
GET /api/v1/export/history/profiles/{profile_id}
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| profile_id | string | 是 | Profile ID |
| limit | integer | 否 | 返回数量，默认 10 |

**响应示例：**

```json
{
  "exported_at": "2026-04-02T10:30:00Z",
  "profile_id": "prof_abc123",
  "profile_updated_at": "2026-04-01T15:00:00Z",
  "resume_count": 3,
  "resumes": [
    {
      "id": "res_yyy",
      "original_filename": "resume_v3.pdf",
      "version": 3,
      "is_current": true,
      "parse_status": "success",
      "created_at": "2026-04-01T10:00:00Z"
    },
    {
      "id": "res_zzz",
      "original_filename": "resume_v2.pdf",
      "version": 2,
      "is_current": false,
      "parse_status": "success",
      "created_at": "2026-03-15T10:00:00Z"
    }
  ]
}
```

---

## 认证

Export API 目前无需认证即可访问。

## 错误

| 状态码 | 说明 |
|--------|------|
| 404 | Profile 或简历不存在 |
| 500 | 服务器内部错误 |

---

*最后更新：2026-04-02*
