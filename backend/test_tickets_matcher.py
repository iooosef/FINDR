"""
test_tickets_matcher.py - Automated tests for Stage 3: Tickets, Matching, Notifications, and Conflicts.
"""

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db

def run_tests():
    # Clean previous test ticket records
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM matches")
        cursor.execute("DELETE FROM notifications")
        cursor.execute("DELETE FROM missing_tickets")
        cursor.execute("DELETE FROM lost_item_tickets")

    # Setup test clients (separate session cookies for student1, student2, and staff)
    staff_client = TestClient(app)
    student1_client = TestClient(app)
    student2_client = TestClient(app)

    print("--- 1. Authenticating test users ---")
    # Login staff
    r = staff_client.post("/api/auth/login", json={"id_number": "admin", "password": "adminpassword123"})
    assert r.status_code == 200, f"Staff login failed: {r.text}"
    print("✅ Staff authenticated")

    # Login student 1
    r = student1_client.post("/api/auth/login", json={"id_number": "2026-0001", "password": "studentpassword123"})
    assert r.status_code == 200, f"Student 1 login failed: {r.text}"
    print("✅ Student 1 authenticated")

    # Login student 2
    r = student2_client.post("/api/auth/login", json={"id_number": "2026-0002", "password": "studentpassword123"})
    assert r.status_code == 200, f"Student 2 login failed: {r.text}"
    print("✅ Student 2 authenticated")

    print("\n--- 2. Student 1 creates Missing Ticket ---")
    missing_data1 = {
        "item_name": "Black Casio scientific calculator",
        "category": "Electronics",
        "brand": "Casio",
        "color": "Black",
        "date_lost": "2026-09-11",
        "time_lost": "Around 10:30 AM",
        "locations": "Library, Canteen",
        "description": "Casio calculator with blue sticker on back cover"
    }
    r = student1_client.post("/api/tickets/missing", data=missing_data1)
    assert r.status_code == 201, f"Create missing ticket failed: {r.text}"
    ticket1_id = r.json()["ticket_id"]
    print(f"✅ Student 1 created Missing Ticket #{ticket1_id}")

    print("\n--- 3. Staff creates Lost Item Ticket (Matching category, brand, and color) ---")
    found_data = {
        "item_name": "Casio fx-991ES Plus calculator",
        "category": "Electronics",
        "brand": "Casio",
        "color": "Black",
        "date_found": "2026-09-11",
        "time_found": "11:00 AM",
        "location_found": "Balbago building room 204",
        "description": "Black scientific calculator found under desk",
        "status": "unclaimed"
    }
    r = staff_client.post("/api/tickets/lost", data=found_data)
    assert r.status_code == 201, f"Create lost item ticket failed: {r.text}"
    found_id = r.json()["item_id"]
    matches_found = r.json()["matches_found"]
    assert matches_found >= 1, "Expected matcher to find at least 1 match"
    print(f"✅ Staff created Lost Item #{found_id} (Matcher found {matches_found} match)")

    print("\n--- 4. Verify Student 1 Notifications and Privacy ---")
    r = student1_client.get("/api/notifications")
    assert r.status_code == 200
    notifs = r.json()["notifications"]
    assert len(notifs) >= 1, "Expected notification for student 1"
    student_notif_text = notifs[0]["message"]
    print(f"✅ Student notification: '{student_notif_text}'")
    # Verify privacy: must NOT reveal found item's location or details
    assert "Balbago building" not in student_notif_text, "Found location should NOT be revealed to student!"
    assert "fx-991ES" not in student_notif_text, "Found item specific name should NOT be revealed to student!"

    print("\n--- 5. Test Conflicting Matches (Student 2 reports another Casio) ---")
    missing_data2 = {
        "item_name": "Casio Calculator",
        "category": "Electronics",
        "brand": "Casio",
        "color": "Black",
        "date_lost": "2026-09-11",
        "locations": "Library",
        "description": "My math calculator"
    }
    r = student2_client.post("/api/tickets/missing", data=missing_data2)
    assert r.status_code == 201
    ticket2_id = r.json()["ticket_id"]
    print(f"✅ Student 2 created Missing Ticket #{ticket2_id}")

    # Check that Lost Item status changed to 'pending_verification' due to multiple matches
    r = staff_client.get(f"/api/tickets/lost/{found_id}")
    assert r.status_code == 200
    item_status = r.json()["item"]["status"]
    assert item_status == "pending_verification", f"Expected 'pending_verification', got '{item_status}'"
    print(f"✅ Conflict handling verified: Lost Item status is now '{item_status}'")

    print("\n--- 6. Staff verifies Student 1 in-person at office ---")
    # Get matches for staff
    r = staff_client.get("/api/matches")
    assert r.status_code == 200
    matches = r.json()["matches"]
    # Find match for Student 1
    match1 = next(m for m in matches if m["missing_ticket_id"] == ticket1_id and m["lost_item_id"] == found_id)
    match2 = next(m for m in matches if m["missing_ticket_id"] == ticket2_id and m["lost_item_id"] == found_id)

    # Verify match 1
    r = staff_client.put(f"/api/matches/{match1['match_id']}/verify")
    assert r.status_code == 200, f"Verify match failed: {r.text}"
    print("✅ Match 1 verified by staff")

    # Check Lost Item is now claimed
    r = staff_client.get(f"/api/tickets/lost/{found_id}")
    assert r.json()["item"]["status"] == "claimed"
    print("✅ Lost Item status is now 'claimed'")

    # Check Student 1 ticket is resolved
    r = student1_client.get(f"/api/tickets/missing/{ticket1_id}")
    assert r.json()["ticket"]["status"] == "resolved"
    print("✅ Student 1 ticket status is now 'resolved'")

    # Check competing match is rejected
    r = staff_client.get("/api/matches")
    m2_updated = next(m for m in r.json()["matches"] if m["match_id"] == match2["match_id"])
    assert m2_updated["match_status"] == "rejected"
    print("✅ Competing match correctly marked as 'rejected'")

    # Check Student 2 ticket remains 'open'
    r = student2_client.get(f"/api/tickets/missing/{ticket2_id}")
    assert r.json()["ticket"]["status"] == "open"
    print("✅ Student 2 ticket remains 'open'")

    print("\n--- 7. Returned Items Table Query ---")
    r = staff_client.get("/api/tickets/returned")
    assert r.status_code == 200
    returned_items = r.json()["items"]
    assert any(item["id"] == found_id for item in returned_items)
    print("✅ Returned items table correctly includes claimed item")

    print("\n🎉 ALL STAGE 3 TICKETS & MATCHER TESTS PASSED PERFECTLY!")


if __name__ == "__main__":
    run_tests()
