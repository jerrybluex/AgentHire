# AgentHire 审计问题台账

更新时间：2026-04-07
维护原则：新增问题必须记录；状态变化必须更新；关闭问题必须保留痕迹。

字段说明：
- 编号：唯一 ID
- 级别：P0 / P1 / P2
- 分类：安全 / 架构 / 流程 / 可靠性 / 测试 / 文档 / 前端 / 部署
- 标题：问题简述
- 定位：文件或模块路径
- 影响：影响范围
- 当前状态：open / in_progress / blocked / done / accepted_risk
- 备注：补充判断

---

## P0

| 编号 | 分类 | 标题 | 定位 | 影响 | 当前状态 | 备注 |
|---|---|---|---|---|---|---|
| P0-001 | 安全 | 仓库存在真实凭证/令牌泄露 | `.env`, `token.txt` | 凭证泄露、账户风险、外部滥用 | open | 需立刻轮换并清理历史传播面 |
| P0-002 | 安全/鉴权 | 多个接口只依赖 Header/参数伪鉴权 | `backend/app/api/deps.py`, `api/v1/*` | 用户/企业/管理员越权 | open | 必须补真实身份验证 |
| P0-003 | 安全/管理面 | 企业管理接口存在未授权风险 | `backend/app/api/v1/enterprise.py` | 企业审核/列表暴露 | open | 优先封禁或加 admin 鉴权 |
| P0-004 | 安全/数据导出 | 导出接口缺少鉴权或所有权校验 | `backend/app/api/v1/export.py` | 候选人资料、简历外泄 | open | 应先下线或加网关白名单 |
| P0-005 | 架构 | 旧身份模型与新身份模型并存 | `backend/app/models/__init__.py`, `api/deps.py` | 权限、审计、归属混乱 | open | 必须尽快确立唯一主线 |
| P0-006 | 流程/代码 | 主链路接口存在阻断性引用错误 | `backend/app/api/v1/applications.py`, `jobs.py` | 企业处理申请、职位维护不稳定 | open | 直接影响主链是否可跑 |
| P0-007 | 流程 | 企业注册存在 legacy/v2 双入口 | `frontend/src/app/enterprise/register/page.tsx`, `backend/app/api/v1/enterprise.py` | 新旧数据继续分叉 | open | 前端应切到统一入口 |
| P0-008 | 可靠性 | 上传流程 Redis 与磁盘状态源不一致 | `backend/app/api/v1/upload.py`, `core/cache.py` | 分片完成判定错误、上传失败 | open | 需统一事实来源 |
| P0-009 | 安全/部署 | Redis/DB/MinIO/Flower 暴露面过大且默认配置危险 | `.env`, `docker-compose*.yml`, `devops/redis/redis.conf` | 公网暴露、接管风险 | open | 先收口部署暴露面 |

---

## P1

| 编号 | 分类 | 标题 | 定位 | 影响 | 当前状态 | 备注 |
|---|---|---|---|---|---|---|
| P1-001 | 文档 | API 文档、README、PRD 与实现不一致 | `docs/api/*`, `README.md`, `docs/PRD.md` | 文档不可作为可信协议 | open | 协议型产品的高优先级问题 |
| P1-002 | 可靠性 | 业务失败仍可能返回 200/201 | `backend/app/api/v1/enterprise.py`, `agents.py` 等 | 前端/监控误判成功 | open | 需统一 HTTP 语义 |
| P1-003 | 可靠性/并发 | 企业配额校验非原子，可能超额 | `backend/app/services/enterprise_service.py` | 计费/配额错误 | open | race condition |
| P1-004 | 架构/模型 | Profile 读写字段定义不一致 | `models/__init__.py`, `api/v1/profiles.py` | 获取资料报错/对象语义混乱 | open | 需统一 schema/model/doc |
| P1-005 | 安全/流程 | 联系方式解锁流程规则未固化 | application/contact unlock 相关模块 | 业务约束不足 | open | 应纳入状态机设计 |
| P1-006 | 测试 | 大量 placeholder/skip 测试，真实保护不足 | `tests/unit/*`, `tests/integration/*` | 回归风险高 | open | 假覆盖问题明显 |
| P1-007 | 前端 | 企业/管理工作台大量演示态数据 | `frontend/src/app/*dashboard*` | 不适合作为真实运营后台 | open | 先服务主链而不是铺页面 |

---

## P2

| 编号 | 分类 | 标题 | 定位 | 影响 | 当前状态 | 备注 |
|---|---|---|---|---|---|---|
| P2-001 | 前端 | 大页面组件过大，状态逻辑分散 | `frontend/src/app/skill/page.tsx` 等 | 可维护性差 | open | 后续拆 hooks / sections |
| P2-002 | 后端 | 超大聚合文件职责混杂 | `models/__init__.py`, `schemas/__init__.py`, `api/v1/*.py` | 维护成本高 | open | 需要领域拆分 |
| P2-003 | 工程 | 启动时 `create_all` 与迁移职责混乱 | `backend/app/main.py` | schema 漂移风险 | open | 应以 Alembic 为主 |
| P2-004 | 前端/工程 | frontend 缺少自动化测试体系 | `frontend/package.json`, `frontend/src` | 页面改动易回归 | open | 后续补 Vitest/RTL 或同类 |
| P2-005 | 监控/限流 | 限流统计 limit 值错误 | `backend/app/core/rate_limit.py` | 运行数据误导 | open | 不影响主功能但影响运维判断 |
| P2-006 | 工程卫生 | 仓库混入日志、数据库、coverage、构建产物 | 多处 | 协作噪音、误提交风险 | open | 需整理 `.gitignore` 与清理策略 |

---

## 状态定义

- `open`：已确认，未开始处理
- `in_progress`：已开始治理
- `blocked`：处理依赖未满足
- `done`：已修复并验证
- `accepted_risk`：经确认暂时接受风险

---

## 使用规则

1. 新发现问题先记台账，再决定是否立刻修。
2. 修复时必须把对应编号写进提交说明或修复记录。
3. 任何人接手时先看本文件，避免重复摸排。
