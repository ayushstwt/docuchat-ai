import pytest
import pytest_asyncio
from app.constants.enums import ActivityAction


@pytest_asyncio.fixture
async def auth_user(client):
    register_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "audituser@example.com", "password": "Password123", "fullName": "Audit User"},
    )
    assert register_res.status_code == 201
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "audituser@example.com", "password": "Password123"},
    )
    token = login_res.json()["data"]["accessToken"]
    return token


@pytest.mark.asyncio
async def test_list_activity_logs_unauthorized(client):
    response = await client.get("/api/v1/activity-logs")
    assert response.status_code == 401
    assert response.json()["errorCode"] == "E008"


@pytest.mark.asyncio
async def test_list_activity_logs_success_and_pagination(client, auth_user):
    token = auth_user

    # Fetch activity logs
    response = await client.get(
        "/api/v1/activity-logs?page=0&size=10",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "metadata" in data
    assert data["metadata"]["currentPage"] == 0
    assert data["metadata"]["pageSize"] == 10
    assert isinstance(data["data"], list)

    # Verify registration/login activity is captured
    activities = data["data"]
    assert len(activities) >= 1
    actions = [a["action"] for a in activities]
    assert "LOGIN" in actions or "REGISTER" in actions


@pytest.mark.asyncio
async def test_activity_logs_isolation_between_users(client):
    # User 1
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user1_audit@example.com", "password": "Password123", "fullName": "User One"},
    )
    login1 = await client.post(
        "/api/v1/auth/login",
        json={"email": "user1_audit@example.com", "password": "Password123"},
    )
    token1 = login1.json()["data"]["accessToken"]

    # User 2
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user2_audit@example.com", "password": "Password123", "fullName": "User Two"},
    )
    login2 = await client.post(
        "/api/v1/auth/login",
        json={"email": "user2_audit@example.com", "password": "Password123"},
    )
    token2 = login2.json()["data"]["accessToken"]

    # Fetch logs for User 1
    res1 = await client.get("/api/v1/activity-logs", headers={"Authorization": f"Bearer {token1}"})
    # Fetch logs for User 2
    res2 = await client.get("/api/v1/activity-logs", headers={"Authorization": f"Bearer {token2}"})

    logs1 = res1.json()["data"]
    logs2 = res2.json()["data"]

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert isinstance(logs1, list)
    assert isinstance(logs2, list)
