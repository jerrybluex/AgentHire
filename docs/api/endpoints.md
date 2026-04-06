# AgentHire API 端点清单

本文档列出所有API端点，供开发和测试参考。标注了实现状态和优先级。

---

## 图例说明

| 标记 | 含义 |
|------|------|
| P0 | 必须实现（MVP核心功能） |
| P1 | 重要功能（第二阶段） |
| P2 | 可选功能（第三阶段） |
| ✅ | 已实现 |
| 🔲 | 未实现 |

---

## 1. 系统端点

### 1.1 健康检查

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| GET | `/health` | 健康检查 | 否 | P0 | ✅ |
| GET | `/api/v1/health` | API健康检查 | 否 | P0 | ✅ |

---

## 2. Agent API（C端）

### 2.1 Agent 注册与认证

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| POST | `/api/v1/agents/register` | 注册Agent | 否 | P0 | ✅ |
| POST | `/api/v1/agents/authenticate` | 认证Agent | 否 | P0 | ✅ |
| GET | `/api/v1/agents/me` | 获取Agent信息 | HMAC | P0 | ✅ |

---

## 3. Skill API（求职/招聘技能）

### 3.1 意图解析

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| POST | `/api/v1/skill/parse-intent` | 解析自然语言意图 | 可选 | P0 | ✅ |

### 3.2 简历解析

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| POST | `/api/v1/skill/parse-resume` | 解析简历文件 | 可选 | P0 | ✅ |

---

## 4. Profile API（C端）

### 4.1 Profile CRUD

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| POST | `/api/v1/profiles` | 创建Profile | HMAC | P0 | ✅ |
| GET | `/api/v1/profiles/{id}` | 获取Profile | HMAC | P0 | ✅ |
| PUT | `/api/v1/profiles/{id}` | 更新Profile | HMAC | P0 | ✅ |
| DELETE | `/api/v1/profiles/{id}` | 删除Profile | HMAC | P0 | ✅ |
| GET | `/api/v1/profiles` | 列表查询 | 否 | P0 | ✅ |

---

## 5. Job API（B端）

### 5.1 职位 CRUD

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| POST | `/api/v1/jobs` | 发布职位 | API Key | P0 | ✅ |
| GET | `/api/v1/jobs/{id}` | 获取职位详情 | 否 | P0 | ✅ |
| PUT | `/api/v1/jobs/{id}` | 更新职位 | API Key | P0 | ✅ |
| DELETE | `/api/v1/jobs/{id}` | 删除职位 | API Key | P0 | ✅ |

---

## 6. Discovery API（Agent自主发现）

### 6.1 自主发现

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| GET | `/api/v1/discover/jobs` | 发现职位 | 否 | P0 | ✅ |
| GET | `/api/v1/discover/profiles` | 发现人才 | API Key | P0 | ✅ |

---

## 7. Enterprise API（企业端）

### 7.1 企业认证

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| POST | `/api/v1/enterprise/apply` | 申请入驻 | 否 | P0 | ✅ |
| POST | `/api/v1/enterprise/login` | 企业登录 | 否 | P0 | ✅ |
| GET | `/api/v1/enterprise` | 企业列表 | admin | P0 | ✅ |
| POST | `/api/v1/enterprise/verify` | 认证审核 | 否 | P0 | ✅ |
| GET | `/api/v1/enterprise/me` | 获取企业信息 | 否 | P0 | ✅ |

### 7.2 API Key 管理

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| POST | `/api/v1/enterprise/api-keys` | 创建API Key | 否 | P0 | ✅ |

---

## 8. Billing API（计费）

### 8.1 计费与账单

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| GET | `/api/v1/billing` | 获取账单 | API Key | P0 | ✅ |
| GET | `/api/v1/billing/stats` | 使用统计 | API Key | P0 | ✅ |
| GET | `/api/v1/billing/pricing` | 计费价格表 | 否 | P0 | ✅ |

---

## 9. Webhook API

### 9.1 Webhook 管理

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| POST | `/api/v1/webhooks` | 注册Webhook | 否 | P0 | ✅ |
| GET | `/api/v1/webhooks` | 获取Webhook列表 | 否 | P0 | ✅ |
| DELETE | `/api/v1/webhooks/{id}` | 删除Webhook | 否 | P0 | ✅ |

---

## 10. A2A 协议 API

### 10.1 A2A 意向表达

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| POST | `/api/v1/a2a/interest` | 表达意向 | HMAC | P0 | ✅ |
| POST | `/api/v1/a2a/interest/respond` | 回应意向 | HMAC | P0 | ✅ |
| GET | `/api/v1/a2a/interest/{profile_id}/{job_id}` | 获取意向 | HMAC | P0 | ✅ |

### 10.2 A2A 谈判

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| POST | `/api/v1/a2a/negotiate` | 薪资谈判 | HMAC | P0 | ✅ |
| POST | `/api/v1/a2a/counter-offer` | 还价 | HMAC | P0 | ✅ |
| POST | `/api/v1/a2a/confirm` | 确认 | HMAC | P0 | ✅ |
| POST | `/api/v1/a2a/reject` | 拒绝 | HMAC | P0 | ✅ |
| GET | `/api/v1/a2a/session/{session_id}` | 获取会话 | HMAC | P0 | ✅ |

---

## 11. Export API（数据导出）

### 11.1 Profile 导出

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| GET | `/api/v1/export/profiles/{id}` | 导出Profile JSON | 否 | P2 | ✅ |
| GET | `/api/v1/export/profiles/{id}/pdf` | 导出Profile PDF | 否 | P2 | ✅ |

### 11.2 简历导出

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| GET | `/api/v1/export/resumes/{id}` | 导出简历 JSON | 否 | P2 | ✅ |
| GET | `/api/v1/export/resumes/{id}/pdf` | 导出简历 PDF | 否 | P2 | ✅ |

### 11.3 导出历史

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| GET | `/api/v1/export/history/profiles/{id}` | 获取导出历史 | 否 | P2 | ✅ |

---

## 12. Users API（用户系统）

### 12.1 用户注册与登录

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| POST | `/api/v1/users/register` | 用户注册 | 否 | P2 | ✅ |
| POST | `/api/v1/users/login` | 用户登录 | 否 | P2 | ✅ |
| GET | `/api/v1/users/me` | 获取用户信息 | 否 | P2 | ✅ |

---

## 13. Claim API（Agent认领）

### 13.1 Agent 认领

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| POST | `/api/v1/claim/agent` | 发起认领 | 否 | P2 | ✅ |
| POST | `/api/v1/claim/verify` | 验证认领 | 否 | P2 | ✅ |
| GET | `/api/v1/claim/status/{agent_id}` | 获取认领状态 | 否 | P2 | ✅ |
| GET | `/api/v1/claim/list` | 列出认领记录 | 否 | P2 | ✅ |

---

## 14. Stats API（统计面板）

### 14.1 使用统计

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| GET | `/api/v1/stats/summary` | 使用摘要 | 否 | P2 | ✅ |
| GET | `/api/v1/stats/trend` | 使用趋势 | 否 | P2 | ✅ |
| GET | `/api/v1/stats/by-type` | 按类型统计 | 否 | P2 | ✅ |
| GET | `/api/v1/stats/api-keys` | 按API Key统计 | 否 | P2 | ✅ |
| GET | `/api/v1/stats/monthly` | 月度统计 | 否 | P2 | ✅ |

---

## 15. Upload API（文件上传）

### 15.1 分片上传

| 方法 | 端点 | 描述 | 认证 | 优先级 | 状态 |
|------|------|------|------|--------|------|
| POST | `/api/v1/upload/init` | 初始化上传 | 否 | P2 | ✅ |
| POST | `/api/v1/upload/chunk` | 上传分片 | 否 | P2 | ✅ |
| POST | `/api/v1/upload/complete` | 完成上传 | 否 | P2 | ✅ |
| GET | `/api/v1/upload/status/{upload_id}` | 获取上传状态 | 否 | P2 | ✅ |
| POST | `/api/v1/upload/cancel` | 取消上传 | 否 | P2 | ✅ |

---

## 统计汇总

### 按优先级统计

| 优先级 | 端点数量 | 已实现 | 实现率 |
|--------|---------|--------|--------|
| P0 | 35 | 35 | 100% |
| P1 | 10 | 0 | 0% |
| P2 | 20 | 20 | 100% |
| **总计** | **65** | **55** | **85%** |

### 按模块统计

| 模块 | 端点数量 | 已实现 |
|------|---------|--------|
| 系统端点 | 2 | 2 |
| Agent API | 3 | 3 |
| Skill API | 2 | 2 |
| Profile API | 5 | 5 |
| Job API | 4 | 4 |
| Discovery API | 2 | 2 |
| Enterprise API | 6 | 6 |
| Billing API | 3 | 3 |
| Webhook API | 3 | 3 |
| A2A 协议 | 8 | 8 |
| Export API | 6 | 6 |
| Users API | 3 | 3 |
| Claim API | 4 | 4 |
| Stats API | 5 | 5 |
| Upload API | 5 | 5 |

---

## 更新记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-04-02 | v2.0 | 全面更新，标记所有已实现端点，补充新API文档 |

---

*本文档由 Documentation Agent 维护，与代码实现保持同步更新。*
