"""
test_auth.py - Test script to verify Stage 2 authentication endpoints and session cookies.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_auth_flow():
    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("✅ Health check passed")

    # 2. Test staff login
    login_payload = {
        "id_number": "admin",
        "password": "adminpassword123"
    }
    res = client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 200, f"Staff login failed: {res.text}"
    staff_data = res.json()
    assert staff_data["user"]["role"] == "staff", "Role should be staff"
    print("✅ Staff login passed:", staff_data["user"]["username"])

    # 3. Test /api/auth/me with staff session
    res = client.get("/api/auth/me")
    assert res.status_code == 200, f"/me failed: {res.text}"
    assert res.json()["user"]["username"] == "admin"
    print("✅ /api/auth/me (staff) passed")

    # 4. Test logout
    res = client.post("/api/auth/logout")
    assert res.status_code == 200
    # Now /me should be 401
    res = client.get("/api/auth/me")
    assert res.status_code == 401, "Expected 401 after logout"
    print("✅ Logout passed (session cleared)")

    # 5. Test student registration
    import random
    random_id = f"2026-{random.randint(1000, 9999)}"
    reg_payload = {
        "name": "Maria Santos",
        "id_number": random_id,
        "password": "password123"
    }
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 201, f"Registration failed: {res.text}"
    student_data = res.json()
    assert student_data["user"]["role"] == "student"
    assert student_data["user"]["username"] == random_id
    print("✅ Student registration passed:", student_data["user"])

    # 6. Verify session cookie auto-login on registration
    res = client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json()["user"]["username"] == random_id
    print("✅ Student session persistence passed")

    # 7. Test invalid login
    res = client.post("/api/auth/login", json={"id_number": random_id, "password": "wrongpassword"})
    assert res.status_code == 401
    print("✅ Invalid password correctly rejected (401)")

    print("\n🎉 ALL STAGE 2 AUTH TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_auth_flow()
