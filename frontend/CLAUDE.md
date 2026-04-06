@AGENTS.md

# AgentHire 前端开发说明

## 页面结构

| 路径 | 角色 | 功能 |
|------|------|------|
| `/` | 所有人 | 落地页（LandingPage.tsx） |
| `/skill` | Agent | Agent 接入文档 |
| `/dashboard` | **管理员** | 平台管理（统计、待审核企业） |
| `/enterprise` | **管理员** | 企业列表 |
| `/enterprise/register` | **企业用户** | 企业入驻注册（上传营业执照等） |
| `/enterprise/dashboard` | **企业用户** | 企业工作台（Agent 接入引导） |
| `/job-seekers` | 管理员 | 求职者管理 |
| `/jobs` | 管理员/企业 | 职位列表 |

## 角色说明

- **普通用户**：访问 `/` 了解平台
- **求职者用户**：复制 `/skill` 页面的指引，发给自己的 Agent
- **企业用户**：通过 `/enterprise/register` 入驻，审核后通过 `/enterprise/dashboard` 管理
- **管理员**：通过 `/dashboard` 审核企业、管理数据

## C 端流程（求职者）

```
首页 → 复制 /skill 指引 → 发给 Agent → Agent 自动注册求职
```

## B 端流程（企业）

```
首页 → 企业入驻(/enterprise/register) → 管理员审核(/dashboard) →
企业登录(/enterprise/dashboard) → 获取 Agent 凭证 → 发给 Agent → Agent 自动招聘
```

## 组件说明

| 组件 | 路径 | 说明 |
|------|------|------|
| LandingPage | `src/components/LandingPage.tsx` | 首页落地页 |
| Header | `src/components/Header.tsx` | 页面头部 |
| Button | `src/components/Button.tsx` | 按钮组件 |
| DataTable | `src/components/DataTable.tsx` | 数据表格 |
| Modal | `src/components/Modal.tsx` | 弹窗组件 |
| StatusBadge | `src/components/StatusBadge.tsx` | 状态标签 |

## API 封装

| 模块 | 路径 | 说明 |
|------|------|------|
| api.ts | `src/lib/api.ts` | API 调用封装，包含 agents/profiles/jobs/enterprises/matching |

## 注意事项

1. **认证机制**：Profile 创建需要 HMAC 签名认证（X-Agent-ID, X-Timestamp, X-Signature）
2. **企业 API**：使用 X-API-Key Header 认证
3. **构建检查**：提交前运行 `npm run build` 确保无错误
