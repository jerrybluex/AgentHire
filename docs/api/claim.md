# Claim API - Agent 认领

Agent 认领 API 允许 C 端用户将 Agent 绑定到自己的账户。

---

## 目录

- [认领流程](#认领流程)
- [发起认领](#发起认领)
- [验证认领](#验证认领)
- [查询认领状态](#查询认领状态)
- [列出认领记录](#列出认领记录)

---

## 认领流程

```
1. 用户发起认领请求 → 获取验证码
2. 用户输入验证码 → 验证通过
3. Agent 绑定到用户账户
```

---

## 发起认领

发起对某个 Agent 的认领请求。

```
POST /api/v1/claim/agent
```

**请求头：**

```
X-User-ID: {user_id}
```

**请求体：**

```json
{
  "agent_id": "agt_abc123"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| agent_id | string | 是 | 要认领的 Agent ID |

**响应示例：**

```json
{
  "success": true,
  "data": {
    "claim_id": "clm_xyz789",
    "agent_id": "agt_abc123",
    "verification_code": "123456",
    "status": "pending",
    "expires_at": "2026-04-03T10:30:00Z"
  }
}
```

**说明：**
- `verification_code` 是 6 位数字验证码
- 验证码有效期为 24 小时
- 验证码应通过短信或邮件发送给用户（本系统仅返回）

**错误：**

| 状态码 | 说明 |
|--------|------|
| 404 | Agent 不存在 |

---

## 验证认领

输入验证码完成认领。

```
POST /api/v1/claim/verify
```

**请求头：**

```
X-User-ID: {user_id}
```

**请求体：**

```json
{
  "agent_id": "agt_abc123",
  "verification_code": "123456"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| agent_id | string | 是 | Agent ID |
| verification_code | string | 是 | 6位验证码 |

**响应示例：**

```json
{
  "success": true,
  "data": {
    "success": true,
    "agent_id": "agt_abc123",
    "claimed_at": "2026-04-02T10:30:00Z"
  }
}
```

**错误：**

| 状态码 | 说明 |
|--------|------|
| 400 | 验证码错误或已过期 |
| 404 | 认领记录不存在 |

---

## 查询认领状态

查询用户对某个 Agent 的认领状态。

```
GET /api/v1/claim/status/{agent_id}
```

**请求头：**

```
X-User-ID: {user_id}
```

**响应示例：**

```json
{
  "success": true,
  "data": {
    "claim_id": "clm_xyz789",
    "agent_id": "agt_abc123",
    "status": "verified",
    "claimed_at": "2026-04-02T10:30:00Z",
    "verified_at": "2026-04-02T10:35:00Z"
  }
}
```

**状态说明：**

| 状态 | 说明 |
|------|------|
| pending | 认领请求已发起，等待验证 |
| verified | 认领已完成 |
| expired | 验证码已过期 |

---

## 列出认领记录

列出用户所有的 Agent 认领记录。

```
GET /api/v1/claim/list
```

**请求头：**

```
X-User-ID: {user_id}
```

**响应示例：**

```json
{
  "success": true,
  "data": [
    {
      "claim_id": "clm_xyz789",
      "agent_id": "agt_abc123",
      "status": "verified",
      "claimed_at": "2026-04-02T10:30:00Z",
      "verified_at": "2026-04-02T10:35:00Z"
    },
    {
      "claim_id": "clm_aaa111",
      "agent_id": "agt_def456",
      "status": "pending",
      "claimed_at": null,
      "verified_at": null
    }
  ]
}
```

---

## 认证

Claim API 使用 `X-User-ID` 请求头传递用户 ID。

---

## 相关文档

- [Users API](users.md) - 用户注册登录

---

*最后更新：2026-04-02*
