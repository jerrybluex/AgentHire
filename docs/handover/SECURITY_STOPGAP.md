# SECURITY_STOPGAP

## 立即止血动作（仓库侧）

本次仅处理**仓库收口**，不在此文档内执行凭证轮换。

### 已落地
- 补强 `.gitignore`，屏蔽以下高风险或运行产物：
  - `token.txt`
  - `.env` / `.env.*`（保留 `*.env.example`）
  - 日志、`coverage/`、`htmlcov/`、`.coverage*`
  - `sqlite/`、`db/`、`*.db`、`*.sqlite*`
  - `uploads/`、`backend/uploads/`
  - `frontend/.next/`、`.next/`
  - `node_modules/`
  - 常见本地临时/备份产物（如 `*.bak`）
- 将已被 Git 跟踪但不应纳入版本管理的运行产物/敏感文件从 **Git 索引** 移除；仅取消跟踪，不删除本地文件。

### 建议立即执行（仓库外）
1. 对历史上可能已暴露的密钥、Token、数据库连接串执行轮换。
2. 检查 CI/CD、部署平台、第三方集成平台是否同步使用了旧凭证。
3. 若公开仓库曾泄露敏感信息，评估是否需要进一步做历史重写（`git filter-repo` / BFG）。
   - 当前提交只解决“继续误提交”的问题，**不清除历史提交中的泄露**。

### 本次策略说明
- 优先采取**最小改动**：
  - 不删除开发者本地 `.env`、上传文件、覆盖率报告；
  - 仅通过 `.gitignore` + `git rm --cached` 让其不再进入版本管理。
- `*.env.example` 继续保留，用于环境变量模板分发。
