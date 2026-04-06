# Users API - 用户系统

用户系统用于 C 端用户认领 Agent，实现用户账户与 Agent 的绑定。

---

## 目录

- [用户注册](#用户注册)
- [用户登录](#用户登录)
- [获取用户信息](#获取用户信息)

---

## 用户注册

创建新的用户账户。

```
POST /api/v1/users/register
```

**请求体：**

```json
{
  "email": "user@example.com",
  "password": "password123",
  "nickname": "张三"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱地址（唯一） |
| password | string | 是 | 密码（至少6位） |
| nickname | string | 否 | 昵称 |

**响应示例：**

```json
{
  "success": true,
  "data": {
    "user_id": "usr_abc123",
    "email": "user@example.com",
    "nickname": "张三"
  }
}
```

**错误：**

| 状态码 | 说明 |
|--------|------|
| 400 | 邮箱已注册或密码太短 |

---

## 用户登录

使用邮箱和密码登录。

```
POST /api/v1/users/login
```

**请求体：**

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应示例：**

```json
{
  "success": true,
  "data": {
    "user_id": "usr_abc123",
    "email": "user@example.com",
    "nickname": "张三"
  }
}
```

**错误：**

| 状态码 | 说明 |
|--------|------|
| 401 | 邮箱或密码错误 |

---

## 获取用户信息

获取当前登录用户的信息。

```
GET /api/v1/users/me?user_id={user_id}
```

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户 ID |

**响应示例：**

```json
{
  "success": true,
  "data": {
    "id": "usr_abc123",
    "email": "user@example.com",
    "nickname": "张三",
    "status": "active",
    "created_at": "2026-04-01T10:00:00Z"
  }
}
```

---

## 认证

Users API 无需认证即可访问。

---

## 相关文档

- [Claim API](claim.md) - Agent 认领流程

---

*最后更新：2026-04-02*
