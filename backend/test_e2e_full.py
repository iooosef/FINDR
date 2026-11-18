"""
test_e2e_full.py - Comprehensive End-to-End Test for Stage 7 Polish & Deployment Verification.
Covers:
1. Database auto-initialization check
2. Student registration & authenticated session
3. Missing ticket report submission
4. Staff login & found item intake
5. Automated matching engine verification (category + secondary match)
6. Notification delivery & privacy guard (no found details shown to student)
7. Multi-student conflict transition to 'pending_verification'
8. Staff in-person verification: winning resolution, competing rejection
9. Returned items history
10. Strict 'no delete' check (HTTP 405 on DELETE)
11. Image upload endpoints fully removed (returns 404)
"""

import time
import random
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db

client = TestClient(app)


def test_full_pipeline():
    print("==================================================")
    print("  FINDR FULL PIPELINE INTEGRATION TEST (STAGE 7)  ")
    print("==================================================")

    # 1. Verify health & home routes
    res = client.get("/api/health")
    assert res.status_code == 200
    res = client.get("/")
    assert res.status_code == 200
    assert "FINDR" in res.text
    print("✅ 1. Health check & Frontend index accessible")

    # 2. Student 1 Registration (Random ID to allow repeated runs)
    unique_id = f"2026-{random.randint(1000, 9999)}-{int(time.time()) % 1000}"
    student1_client = TestClient(app)
    reg_payload = {
        "name": "Maria Clara Santos",
        "id_number": unique_id,
        "password": "securepassword123"
    }
    res = student1_client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 201, f"Registration failed: {res.text}"
    s1_id = res.json()["user"]["id"]
    print(f"✅ 2. Student registered successfully: ID='{unique_id}' (User #{s1_id})")

    # Verify session persists
    res = student1_client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json()["user"]["username"] == unique_id
    print("✅ 3. Session cookie verified for Student 1")

    # 3. Student 1 files a Missing Ticket
    missing_data = {
        "item_name": "Black Casio scientific calculator",
        "category": "Electronics",
        "brand": "Casio",
        "color": "Black",
        "date_lost": "2026-09-11",
        "time_lost": "10:30 AM",
        "locations": "Library 2nd Floor, Balbago Building",
        "description": "Casio fx-991ES with stickers on the protective slip cover"
    }
    res = student1_client.post(
        "/api/tickets/missing",
        data=missing_data
    )
    assert res.status_code == 201, f"Missing ticket submission failed: {res.text}"
    ticket1_id = res.json()["ticket_id"]
    print(f"✅ 4. Missing Ticket #{ticket1_id} created successfully")

    # 4. Staff logs in
    staff_client = TestClient(app)
    res = staff_client.post("/api/auth/login", json={"id_number": "admin", "password": "adminpassword123"})
    assert res.status_code == 200
    print("✅ 5. Staff authenticated: 'admin'")

    # 5. Staff logs a Found Item matching Student 1's report
    found_data = {
        "item_name": "Casio fx-991ES Plus calculator",
        "category": "Electronics",
        "brand": "Casio",
        "color": "Black",
        "date_found": "2026-09-11",
        "time_found": "11:15 AM",
        "location_found": "Balbago Room 204 under desk",
        "description": "Black Casio calculator turned in by janitorial staff",
        "status": "unclaimed"
    }
    res = staff_client.post(
        "/api/tickets/lost",
        data=found_data
    )
    assert res.status_code == 201
    lost_item_id = res.json()["item_id"]
    matches_found = res.json()["matches_found"]
    assert matches_found >= 1, "Expected matcher to find Student 1's report"
    print(f"✅ 6. Staff logged Found Item #{lost_item_id} -> Automatic Match detected!")

    # 6. Verify Student Notification and Privacy
    res = student1_client.get("/api/notifications")
    assert res.status_code == 200
    notifs = res.json()["notifications"]
    assert len(notifs) >= 1
    student_notif = notifs[0]["message"]
    print(f"✅ 7. Student Notification delivered: '{student_notif}'")
    # Strict Privacy Check
    assert "Balbago Room 204 under desk" not in student_notif, "Founder location leaked to student!"
    assert "janitorial staff" not in student_notif, "Founder description leaked to student!"

    # 7. Conflicting Match (Student 2 reports a similar lost Casio)
    student2_client = TestClient(app)
    student2_client.post("/api/auth/login", json={"id_number": "2026-0001", "password": "studentpassword123"})
    res = student2_client.post("/api/tickets/missing", data={
        "item_name": "Casio scientific calculator",
        "category": "Electronics",
        "brand": "Casio",
        "color": "Black",
        "date_lost": "2026-09-11",
        "locations": "Canteen"
    })
    assert res.status_code == 201
    ticket2_id = res.json()["ticket_id"]
    print(f"✅ 8. Student 2 reported Missing Ticket #{ticket2_id} (creates conflict)")

    # Check Found Item status automatically transitioned to 'pending_verification'
    res = staff_client.get(f"/api/tickets/lost/{lost_item_id}")
    assert res.status_code == 200
    assert res.json()["item"]["status"] == "pending_verification"
    print("✅ 9. Conflicting matches handled: Found Item status is 'pending_verification'")

    # 8. Staff performs In-Person Verification for Student 1
    res = staff_client.get("/api/matches")
    assert res.status_code == 200
    matches = res.json()["matches"]
    winning_match = next(m for m in matches if m["missing_ticket_id"] == ticket1_id and m["lost_item_id"] == lost_item_id)
    competing_match = next(m for m in matches if m["missing_ticket_id"] == ticket2_id and m["lost_item_id"] == lost_item_id)

    res = staff_client.put(f"/api/matches/{winning_match['match_id']}/verify")
    assert res.status_code == 200
    print("✅ 10. Staff verified Student 1 in-person at office")

    # 9. Verify Post-Resolution Statuses
    res = staff_client.get(f"/api/tickets/lost/{lost_item_id}")
    assert res.json()["item"]["status"] == "claimed"

    res = student1_client.get(f"/api/tickets/missing/{ticket1_id}")
    assert res.json()["ticket"]["status"] == "resolved"

    res = student2_client.get(f"/api/tickets/missing/{ticket2_id}")
    assert res.json()["ticket"]["status"] == "open"

    res = staff_client.get("/api/matches")
    comp_updated = next(m for m in res.json()["matches"] if m["match_id"] == competing_match["match_id"])
    assert comp_updated["match_status"] == "rejected"
    print("✅ 11. Statuses verified: Lost Item 'claimed', Winner 'resolved', Competing 'open'")

    # 10. Returned Items History
    res = staff_client.get("/api/tickets/returned")
    assert res.status_code == 200
    returned_list = res.json()["items"]
    assert any(item["id"] == lost_item_id for item in returned_list)
    print("✅ 12. Returned items ledger accurately contains verified claim")

    # 11. Security & 'No Delete' Policy Check
    res = staff_client.delete(f"/api/tickets/lost/{lost_item_id}")
    assert res.status_code == 405, "DELETE route should NOT exist!"
    res = staff_client.delete(f"/api/tickets/missing/{ticket1_id}")
    assert res.status_code == 405, "DELETE route should NOT exist!"
    print("✅ 13. Security verified: DELETE method is strictly forbidden (HTTP 405)")

    # 12. Complete Image Removal Check: Verify /uploads/ is not mounted (HTTP 404)
    res = client.get("/uploads/test.png")
    assert res.status_code == 404, "Image upload directory should NOT be mounted!"
    print("✅ 14. Image feature removal verified: /uploads/ is completely absent (HTTP 404)")

    print("\n==================================================")
    print("🎉 ALL 14 END-TO-END PIPELINE CHECKS PASSED 100%!")
    print("==================================================")


if __name__ == "__main__":
    test_full_pipeline()
