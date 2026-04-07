# Project Takeover Governance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 建立 AgentHire 的接手治理系统，确保后续修复、重构、交接都有统一入口、问题台账、决策记录和分阶段路线图。

**Architecture:** 本次不直接修改业务逻辑，先建立项目治理层。通过 handover 文档、问题台账、决策日志和路线图，把“接手结论”沉淀为持续维护资产。后续所有修复任务都必须映射到该治理层。

**Tech Stack:** Markdown, Git, 项目文档体系

---

### Task 1: 创建交接文档目录结构

**Files:**
- Create: `docs/handover/`
- Create: `docs/plans/`

**Step 1: Verify directories do not already exist or are suitable for reuse**

Run: `py -c "from pathlib import Path; root=Path(r'C:\Users\MLTZ\AgentHire'); print((root/'docs'/'handover').exists(), (root/'docs'/'plans').exists())"`
Expected: prints booleans

**Step 2: Create the directories**

Run: `py -c "from pathlib import Path; root=Path(r'C:\Users\MLTZ\AgentHire'); [(root/p).mkdir(parents=True, exist_ok=True) for p in ['docs/handover','docs/plans']]"`
Expected: no error

**Step 3: Verify directories exist**

Run: `py -c "from pathlib import Path; root=Path(r'C:\Users\MLTZ\AgentHire'); print((root/'docs'/'handover').is_dir(), (root/'docs'/'plans').is_dir())"`
Expected: `True True`

**Step 4: Commit**

```bash
git add docs/handover docs/plans
git commit -m "docs: add project takeover governance directories"
```

### Task 2: 编写项目接手总入口文档

**Files:**
- Create: `docs/handover/PROJECT_HANDOVER.md`
- Test: manual review of rendered markdown

**Step 1: Write the handover document**

Document must include:
- 项目一句话定义
- 当前接手结论
- P0/P1/P2 优先级判断
- 唯一可信主链
- 管理原则
- 核心风险总览
- 新负责人阅读顺序
- 当前阶段目标

**Step 2: Review the document for clarity**

Run: `type docs\handover\PROJECT_HANDOVER.md`
Expected: markdown contains all required sections

**Step 3: Commit**

```bash
git add docs/handover/PROJECT_HANDOVER.md
git commit -m "docs: add project handover overview"
```

### Task 3: 建立问题台账

**Files:**
- Create: `docs/handover/AUDIT_LOG.md`

**Step 1: Write the issue register**

Document must include:
- 字段定义
- P0/P1/P2 三层问题表
- 编号/分类/定位/状态/备注
- 状态定义
- 使用规则

**Step 2: Seed the initial known issues**

Include at minimum:
- 凭证泄露
- 伪鉴权
- legacy/v2 双入口
- 主链路阻断 bug
- 上传一致性问题
- 文档漂移
- placeholder 测试

**Step 3: Review for traceability**

Run: `type docs\handover\AUDIT_LOG.md`
Expected: each issue has ID + path + status

**Step 4: Commit**

```bash
git add docs/handover/AUDIT_LOG.md
git commit -m "docs: add audit issue register"
```

### Task 4: 建立关键决策日志

**Files:**
- Create: `docs/handover/DECISIONS.md`

**Step 1: Write the decision log**

Include at minimum:
- 治理总原则
- 与老板的协作机制
- 交接文档是一等产物
- 唯一可信主链
- 身份体系收口方向（标注待落地/待确认边界）
- 文档即协议

**Step 2: Review wording for decision clarity**

Run: `type docs\handover\DECISIONS.md`
Expected: each decision has date, status, decision, reason, impact

**Step 3: Commit**

```bash
git add docs/handover/DECISIONS.md
git commit -m "docs: add project decision log"
```

### Task 5: 建立阶段路线图

**Files:**
- Create: `docs/handover/ROADMAP_V1.md`

**Step 1: Write the roadmap**

Must include:
- 24小时止血
- 1周收口
- 1个月建主链
- 每阶段目标/任务/完成标准
- 暂不优先事项
- 管理规则

**Step 2: Review roadmap for alignment with handover doc**

Run: `type docs\handover\ROADMAP_V1.md`
Expected: phases align with PROJECT_HANDOVER priorities

**Step 3: Commit**

```bash
git add docs/handover/ROADMAP_V1.md
git commit -m "docs: add takeover roadmap v1"
```

### Task 6: 写入总实施计划文件

**Files:**
- Create: `docs/plans/2026-04-07-project-takeover-plan.md`

**Step 1: Write this implementation plan file**

Must include exact tasks for building governance assets.

**Step 2: Review for zero-context readability**

Run: `type docs\plans\2026-04-07-project-takeover-plan.md`
Expected: engineer can execute without extra explanation

**Step 3: Commit**

```bash
git add docs/plans/2026-04-07-project-takeover-plan.md
git commit -m "docs: add takeover implementation plan"
```

### Task 7: Link governance docs into future execution workflow

**Files:**
- Modify: `docs/handover/PROJECT_HANDOVER.md`
- Modify: `docs/handover/AUDIT_LOG.md`
- Modify: `docs/handover/DECISIONS.md`
- Modify: `docs/handover/ROADMAP_V1.md`

**Step 1: Add cross-references if missing**

Ensure each file references the others where appropriate.

**Step 2: Review consistency**

Run: `py -c "from pathlib import Path; root=Path(r'C:\Users\MLTZ\AgentHire\docs\handover');
for p in root.glob('*.md'):
    print('\n==', p.name, '==');
    print(p.read_text(encoding='utf-8')[:400])"`
Expected: all docs exist and are internally consistent

**Step 3: Commit**

```bash
git add docs/handover/*.md
git commit -m "docs: cross-link takeover governance docs"
```

### Task 8: Final verification and checkpoint commit

**Files:**
- Verify: `docs/handover/*.md`
- Verify: `docs/plans/2026-04-07-project-takeover-plan.md`

**Step 1: Run git status**

Run: `git status --short`
Expected: only intended documentation changes are staged or visible

**Step 2: Read the five key files in order**

Read in order:
1. `docs/handover/PROJECT_HANDOVER.md`
2. `docs/handover/AUDIT_LOG.md`
3. `docs/handover/DECISIONS.md`
4. `docs/handover/ROADMAP_V1.md`
5. `docs/plans/2026-04-07-project-takeover-plan.md`

Expected: a new负责人 can understand the project without re-doing discovery.

**Step 3: Commit**

```bash
git add docs/handover docs/plans
git commit -m "docs: establish project takeover operating system"
```
