import pytest
from httpx import AsyncClient
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_auth_end_to_end_flow(client: AsyncClient):
    # 1. Register
    reg_payload = {
        "email": "alice@example.com",
        "password": "Password123",
        "fullName": "Alice Doe",
    }
    res_reg = await client.post("/api/v1/auth/register", json=reg_payload)
    assert res_reg.status_code == 201
    data_reg = res_reg.json()
    assert data_reg["status"] == "success"
    assert data_reg["data"]["email"] == "alice@example.com"
    assert data_reg["data"]["fullName"] == "Alice Doe"
    assert "password" not in data_reg["data"]
    assert "passwordHash" not in data_reg["data"]
    assert res_reg.headers.get("Location") is not None

    # 2. Login
    login_payload = {
        "email": "alice@example.com",
        "password": "Password123",
    }
    res_login = await client.post("/api/v1/auth/login", json=login_payload)
    assert res_login.status_code == 200
    data_login = res_login.json()
    assert data_login["status"] == "success"
    access_token = data_login["data"]["accessToken"]
    refresh_token = data_login["data"]["refreshToken"]
    assert access_token is not None
    assert refresh_token is not None

    # 3. /auth/me
    headers = {"Authorization": f"Bearer {access_token}"}
    res_me = await client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 200
    data_me = res_me.json()
    assert data_me["status"] == "success"
    assert data_me["data"]["email"] == "alice@example.com"

    # 4. Refresh token
    res_ref = await client.post("/api/v1/auth/refresh", json={"refreshToken": refresh_token})
    assert res_ref.status_code == 200
    data_ref = res_ref.json()
    assert data_ref["data"]["accessToken"] is not None


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "email": "bob@example.com",
        "password": "Password123",
        "fullName": "Bob Smith",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    json_data = res2.json()
    assert json_data["status"] == "error"
    assert json_data["errorCode"] == "E006"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    # Non-existent email
    res1 = await client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "Password123"})
    assert res1.status_code == 401
    assert res1.json()["errorCode"] == "E007"

    # Wrong password
    await client.post(
        "/api/v1/auth/register",
        json={"email": "charlie@example.com", "password": "Password123", "fullName": "Charlie"},
    )
    res2 = await client.post(
        "/api/v1/auth/login",
        json={"email": "charlie@example.com", "password": "WrongPassword123"},
    )
    assert res2.status_code == 401
    assert res2.json()["errorCode"] == "E007"


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    # Password too short / missing digits
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "short", "fullName": "Weak"},
    )
    assert res.status_code == 400
    json_data = res.json()
    assert json_data["status"] == "error"
    assert json_data["errorCode"] == "E005"
    assert any(e["field"] == "password" for e in json_data["errors"])


@pytest.mark.asyncio
async def test_invalid_or_expired_token(client: AsyncClient):
    # Invalid token string
    res = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert res.status_code == 401
    assert res.json()["errorCode"] == "E008"

    # Valid signature but non-existent user id
    ghost_token = create_access_token(999999)
    res_ghost = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {ghost_token}"})
    assert res_ghost.status_code == 401
    assert res_ghost.json()["errorCode"] == "E008"
