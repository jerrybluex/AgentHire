#!/usr/bin/env python3
"""手动测试流程 - 企业注册 + 发布职位 + Agent求职"""
import httpx
import hashlib
import hmac
import time

BASE_URL = "http://127.0.0.1:8000"

def main():
    # ==================== 流程1: 企业注册 ====================
    print("=" * 50)
    print("【流程1】企业注册")
    print("=" * 50)

    resp = httpx.post(f"{BASE_URL}/api/v1/enterprise/register", json={
        "company_name": "测试科技公司",
        "unified_social_credit_code": "91110106MA01ABCD12",
        "contact_name": "张三",
        "contact_phone": "13800138000",
        "contact_email": "test@example.com",
        "password": "test123"
    })
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.text}")

    if resp.status_code == 200:
        data = resp.json()
        if data.get("success"):
            print("✅ 企业注册成功！")

            # ==================== 流程2: 管理员审核企业 ====================
            print("\n" + "=" * 50)
            print("【流程2】管理员审核企业（自动批准）")
            print("=" * 50)

            # 模拟管理员直接审核
            resp = httpx.post(f"{BASE_URL}/api/v1/enterprise/verify", json={
                "enterprise_id": data["data"].get("enterprise_id"),
                "status": "approved",
                "admin_notes": "Test approval"
            })
            print(f"状态码: {resp.status_code}")
            print(f"响应: {resp.text}")

            # ==================== 流程3: 企业登录获取API Key ====================
            print("\n" + "=" * 50)
            print("【流程3】企业登录获取API Key")
            print("=" * 50)

            resp = httpx.post(f"{BASE_URL}/api/v1/enterprise/login", json={
                "email": "test@example.com",
                "password": "test123"
            })
            print(f"状态码: {resp.status_code}")
            print(f"响应: {resp.json()}")

            if resp.status_code == 200:
                login_data = resp.json()
                api_key = login_data.get("data", {}).get("api_key")

                # ==================== 流程4: 发布职位 ====================
                print("\n" + "=" * 50)
                print("【流程4】企业发布职位")
                print("=" * 50)

                resp = httpx.post(
                    f"{BASE_URL}/api/v1/jobs",
                    headers={"X-API-Key": api_key},
                    json={
                        "title": "Python 后端工程师",
                        "description": "负责后端API开发，需要熟悉Python/FastAPI",
                        "requirements": ["Python", "FastAPI", "PostgreSQL"],
                        "location": "北京",
                        "salary_range": "20k-35k",
                        "status": "active"
                    }
                )
                print(f"状态码: {resp.status_code}")
                print(f"响应: {resp.text}")

                if resp.status_code in [200, 201]:
                    job_data = resp.json()
                    job_id = job_data.get("data", {}).get("job_id") or job_data.get("data", {}).get("id")
                    print(f"✅ 职位发布成功！Job ID: {job_id}")

                    # ==================== 流程5: Agent求职 ====================
                    print("\n" + "=" * 50)
                    print("【流程5】Agent注册")
                    print("=" * 50)

                    resp = httpx.post(f"{BASE_URL}/api/v1/agents/register", json={
                        "name": "seeker-agent-001",
                        "type": "seeker",
                        "platform": "manual-test"
                    })
                    print(f"状态码: {resp.status_code}")
                    agent_data = resp.json()
                    print(f"响应: {agent_data}")

                    if agent_data.get("success"):
                        agent_id = agent_data["data"]["agent_id"]
                        agent_secret = agent_data["data"]["agent_secret"]
                        print(f"✅ Agent注册成功！Agent ID: {agent_id}")

                        # ==================== 流程6: 创建Profile ====================
                        print("\n" + "=" * 50)
                        print("【流程6】Agent创建Profile")
                        print("=" * 50)

                        timestamp = int(time.time())
                        message = f"{agent_id}{timestamp}"
                        signature = hmac.new(
                            agent_secret.encode(),
                            message.encode(),
                            hashlib.sha256
                        ).hexdigest()

                        resp = httpx.post(
                            f"{BASE_URL}/api/v1/profiles",
                            headers={
                                "X-Agent-ID": agent_id,
                                "X-Timestamp": str(timestamp),
                                "X-Signature": signature
                            },
                            json={
                                "profile": {
                                    "nickname": "李四",
                                    "title": "Python工程师",
                                    "skills": ["Python", "FastAPI", "PostgreSQL"],
                                    "experience_years": 3,
                                    "location": "北京",
                                    "bio": "3年Python后端开发经验"
                                }
                            }
                        )
                        print(f"状态码: {resp.status_code}")
                        print(f"响应: {resp.text}")

                        if resp.status_code == 201:
                            profile_data = resp.json()
                            profile_id = profile_data.get("data", {}).get("profile_id")
                            print(f"✅ Profile创建成功！Profile ID: {profile_id}")

                            # ==================== 流程7: 表达意向 ====================
                            print("\n" + "=" * 50)
                            print("【流程7】Agent表达求职意向")
                            print("=" * 50)

                            resp = httpx.post(
                                f"{BASE_URL}/api/v1/a2a/a2a/interest",
                                json={
                                    "profile_id": profile_id,
                                    "job_id": job_id,
                                    "message": "我对这个职位很感兴趣，希望能进一步沟通！"
                                }
                            )
                            print(f"状态码: {resp.status_code}")
                            print(f"响应: {resp.text}")

                            if resp.status_code in [200, 201]:
                                print("✅ 求职意向表达成功！")
                            else:
                                print(f"❌ 求职意向表达失败")
                        else:
                            print(f"❌ Profile创建失败")
                    else:
                        print(f"❌ Agent注册失败")
        else:
            print(f"❌ 企业注册失败: {data.get('message')}")
    else:
        print(f"❌ 企业注册失败，状态码: {resp.status_code}")

    # ==================== 汇总信息 ====================
    print("\n" + "=" * 50)
    print("【测试完成】")
    print("=" * 50)
    print("\n你可以打开浏览器访问：")
    print(f"  - 前端: http://127.0.0.1:3000/")
    print(f"  - 后端API: http://127.0.0.1:8000/docs")
    print(f"  - 管理后台: http://127.0.0.1:3000/dashboard")

if __name__ == "__main__":
    main()
