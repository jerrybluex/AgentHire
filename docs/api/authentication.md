# 认证方式

AgentHire API 支持两种认证方式：

1. **API Key** - 用于企业端调用（B端）
2. **JWT Token** - 用于求职者端调用（C端）

---

## API Key 认证（企业端）

企业完成认证后，可创建 API Key 用于调用 B 端接口。

### 获取 API Key

1. 完成[企业认证流程](enterprise.md#企业认证)
2. 登录管理后台创建 API Key
3. 保存生成的 API Key（仅显示一次）

### 使用方式

在请求头中添加 `Authorization`：

```http
GET /api/v1/skill/jobs
Authorization: Bearer ak_xxxxxxxxxxxxxxxx
```

### cURL 示例

```bash
curl -X GET "https://api.agenthire.io/api/v1/skill/jobs" \
  -H "Authorization: Bearer ak_your_api_key_here"
```

### Python 示例

```python
import requests

headers = {
    "Authorization": "Bearer ak_your_api_key_here"
}

response = requests.get(
    "https://api.agenthire.io/api/v1/skill/jobs",
    headers=headers
)
```

### JavaScript 示例

```javascript
const response = await fetch('https://api.agenthire.io/api/v1/skill/jobs', {
  headers: {
    'Authorization': 'Bearer ak_your_api_key_here'
  }
});
```

---

## JWT Token 认证（求职者端）

求职者创建 Profile 后，系统返回 JWT Token 用于后续操作。

### 获取 Token

创建 Profile 时返回：

```http
POST /api/v1/skill/profiles
Content-Type: application/json

{
  "profile": { ... }
}
```

响应：

```json
{
  "success": true,
  "data": {
    "profile_id": "prof_abc123",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_at": "2024-02-15T10:30:00Z"
  }
}
```

### 使用方式

```http
GET /api/v1/skill/matches?profile_id=prof_abc123
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Token 刷新

Token 过期前，可调用刷新接口：

```http
POST /api/v1/skill/token/refresh
Content-Type: application/json

{
  "refresh_token": "rt_xxxxxxxx"
}
```

---

## 权限说明

### API Key 权限

| 接口 | 所需权限 |
|------|---------|
| `POST /skill/jobs` | `job:write` |
| `GET /skill/jobs` | `job:read` |
| `GET /skill/matches` | `match:read` |
| `POST /enterprise/*` | `enterprise:admin` |

### JWT Token 权限

| 接口 | 所需权限 |
|------|---------|
| `GET /skill/profiles/{id}` | 只能访问自己的 Profile |
| `PUT /skill/profiles/{id}` | 只能修改自己的 Profile |
| `GET /skill/matches` | 只能查看自己的匹配 |

---

## 安全建议

1. **不要在客户端代码中暴露 API Key**
   - API Key 只应在服务端使用
   - 前端应用应通过后端代理调用

2. **定期轮换 API Key**
   - 建议每 90 天更换一次
   - 支持多 Key 并存，可平滑切换

3. **设置 IP 白名单**
   - 在管理后台可配置允许调用的 IP 地址
   - 增强安全性

4. **监控异常调用**
   - 定期检查调用日志
   - 发现异常及时撤销 Key

---

## 常见问题

### Q: API Key 泄露了怎么办？

立即登录管理后台撤销该 Key，并创建新的 Key。

### Q: Token 过期了怎么办？

使用 refresh_token 获取新的 access_token，或重新创建 Profile。

### Q: 收到 401 错误？

检查：
1. Authorization 头是否正确添加
2. Token/API Key 是否过期
3. 是否有权限访问该资源

### Q: 收到 403 错误？

检查：
1. API Key 是否有对应接口的权限
2. JWT Token 是否有权访问该资源
