#!/usr/bin/env python3
"""
AgentHire 求职流程测试脚本
"""
import httpx
import hashlib
import hmac
import time
import json

BASE_URL = "http://127.0.0.1:8000"

def calc_signature(agent_secret: str, agent_id: str, timestamp: int) -> str:
    """计算 HMAC-SHA256 签名"""
    message = f"{agent_id}{timestamp}"
    signature = hmac.new(
        agent_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def main():
    # Step 1: 注册 Agent
    print("=== Step 1: Register Agent ===")
    resp = httpx.post(f"{BASE_URL}/api/v1/agents/register", json={
        "name": "test-seeker-agent",
        "type": "seeker",
        "platform": "claude"
    })
    print(resp.json())

    data = resp.json()
    if not data.get("success"):
        print("Registration failed!")
        return

    agent_id = data["data"]["agent_id"]
    agent_secret = data["data"]["agent_secret"]
    print(f"Agent ID: {agent_id}")

    # Step 2: 认证 Agent
    print("\n=== Step 2: Authenticate Agent ===")
    timestamp = int(time.time())
    signature = calc_signature(agent_secret, agent_id, timestamp)

    resp = httpx.post(f"{BASE_URL}/api/v1/agents/authenticate", json={
        "agent_id": agent_id,
        "timestamp": timestamp,
        "signature": signature
    })
    print(resp.json())

    # Step 3: 创建 Profile
    print("\n=== Step 3: Create Profile ===")
    timestamp = int(time.time())
    signature = calc_signature(agent_secret, agent_id, timestamp)

    headers = {
        "Content-Type": "application/json",
        "X-Agent-ID": agent_id,
        "X-Timestamp": str(timestamp),
        "X-Signature": signature
    }

    resp = httpx.post(
        f"{BASE_URL}/api/v1/profiles",
        headers=headers,
        json={
            "profile": {
                "nickname": "张三",
                "title": "全栈工程师",
                "skills": ["Python", "FastAPI", "React", "PostgreSQL"],
                "experience_years": 5,
                "location": "北京",
                "bio": "5年全栈开发经验，擅长Python后端和React前端"
            }
        }
    )
    print(resp.json())

    # Step 4: 发现职位
    print("\n=== Step 4: Discover Jobs ===")
    resp = httpx.get(f"{BASE_URL}/api/v1/discover/jobs?location=北京")
    print(resp.json())

    # Step 5: 获取所有可用职位
    print("\n=== Step 5: List All Jobs ===")
    resp = httpx.get(f"{BASE_URL}/api/v1/jobs")
    print(resp.json())

if __name__ == "__main__":
    main()
