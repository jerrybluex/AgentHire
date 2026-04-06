# AgentHire agent_secret 安全修复设计规格

## 状态：已实施 ✅

> **更新**：经过实际代码审查，发现代码**已经实现了加密存储**。审计报告中的"明文存储"描述有误。以下是实际实现的说明和必要的修正。

## 实际代码分析

### 当前实现（正确）

```python
# agent_service.py - register()
agent_secret_hash=encrypt_value(agent_secret, purpose="agent_secret")

# agent_service.py - authenticate()
decrypted_secret = decrypt_value(agent.agent_secret_hash, purpose="agent_secret")
expected_signature = hmac.new(decrypted_secret.encode(), ...)
```

**实现正确**：
- ✅ `agent_secret` 用 Fernet 加密后存储
- ✅ 认证时解密，用解密后的明文计算 HMAC
- ✅ 使用 timing-safe 的 `hmac.compare_digest`

### 实际安全问题

| 问题 | 严重度 | 状态 |
|------|--------|------|
| **字段名误导** | 🟡 中 | ✅ 已修复 |
| 字段名 `agent_secret_hash` 暗示是哈希，实际是密文 | | |
| **config 默认密钥** | 🟡 中 | ⚠️ 部分处理 |
| 生产环境强制检查 `SECURITY_SECRET_KEY`，但默认值处理可改进 | | |

## 实施的修改

### 修改 1：字段改名

**文件**: `backend/app/models/__init__.py`

```python
# 旧
agent_secret_hash: Mapped[str] = mapped_column(String(256), nullable=False)

# 新
api_secret_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
```

### 修改 2：更新 agent_service.py

**文件**: `backend/app/services/agent_service.py`

```python
# 旧
agent.agent_secret_hash=encrypt_value(...)

# 新
agent.api_secret_encrypted=encrypt_value(...)
```

```python
# 旧
decrypted_secret = decrypt_value(agent.agent_secret_hash, ...)

# 新
decrypted_secret = decrypt_value(agent.api_secret_encrypted, ...)
```

### 修改 3：添加安全测试

**文件**: `tests/unit/test_security.py`

新增 `TestAgentSecretEncryption` 测试类：

| 测试 | 验证内容 |
|------|----------|
| `test_agent_secret_is_encrypted_not_plaintext` | 存储的是密文不是明文 |
| `test_agent_secret_can_be_decrypted` | 加密后可以解密 |
| `test_encrypted_agent_secret_requires_correct_purpose` | 错误 purpose 无法解密 |
| `test_hmac_verification_works_after_decryption` | 解密后 HMAC 验证正确 |
| `test_hmac_fails_with_wrong_secret` | 错误密钥 HMAC 验证失败 |

## 架构确认

### Fernet 加密流程

```
注册流程：
1. 生成 api_secret = "as_{random}"
2. 加密：encrypted = Fernet.encrypt(api_secret)
3. 存储：api_secret_encrypted = encrypted
4. 返回：api_secret（仅此一次）

认证流程：
1. 获取：encrypted = api_secret_encrypted
2. 解密：api_secret = Fernet.decrypt(encrypted)
3. 计算：signature = HMAC(api_secret, message)
4. 验证：timing_safe_compare(signature, expected)
```

### 密钥管理

- **开发环境**：自动生成临时密钥（重启后失效，数据不持久）
- **生产环境**：`SECURITY_SECRET_KEY` 必须设置，否则启动失败

## 向后兼容

- 旧字段 `agent_secret_hash` 已改名为 `api_secret_encrypted`
- 需要数据库迁移：更新列名
- 迁移期间：兼容处理新旧字段名

## 待办

- [ ] 数据库迁移脚本（`agent_secret_hash` → `api_secret_encrypted`）
- [ ] 旧数据迁移（加密现有明文/哈希存储的值）
