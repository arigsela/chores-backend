# app/tests/test_endpoints.py
from fastapi.testclient import TestClient
from datetime import date, timedelta

def test_create_child(client):
    response = client.post(
        "/api/children/",
        json={"name": "Charlie", "weekly_allowance": 12.0}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Charlie"
    assert data["weekly_allowance"] == 12.0
    assert "id" in data

def test_get_children(client, sample_data):
    response = client.get("/api/children/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(child["name"] == "Alice" for child in data)
    assert any(child["name"] == "Bob" for child in data)

def test_get_child(client, sample_data):
    alice_id = sample_data["children"]["alice"].id
    response = client.get(f"/api/children/{alice_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alice"

def test_create_chore(client):
    response = client.post(
        "/api/chores/",
        json={
            "name": "Feed Pet",
            "description": "Feed the pet and refresh water"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Feed Pet"

def test_get_chores(client, sample_data):
    response = client.get("/api/chores/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert any(chore["name"] == "Clean Room" for chore in data)

def test_assign_weekly_chores(client, sample_data):
    child_id = sample_data["children"]["alice"].id
    chore_ids = [chore.id for chore in sample_data["chores"]]
    
    # Create the proper request payload
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    response = client.post(
        "/api/weekly-assignments/",  # Remove the query parameter
        json={
            "child_id": child_id,
            "chore_ids": chore_ids,
            "week_start": week_start.isoformat()  # Convert date to string
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(assignment["child_id"] == child_id for assignment in data)

def test_get_weekly_assignments(client, sample_data):
    child_id = sample_data["children"]["alice"].id
    response = client.get(f"/api/weekly-assignments/{child_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(assignment["child_id"] == child_id for assignment in data)

def test_complete_assignment(client, sample_data):
    assignment_id = sample_data["assignments"][0].id
    response = client.put(f"/api/assignments/{assignment_id}/complete")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "completed_date" in data

def test_get_assignment_history(client, sample_data):
    child_id = sample_data["children"]["alice"].id
    response = client.get(f"/api/assignments/history/{child_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_delete_assignment(client, sample_data):
    assignment_id = sample_data["assignments"][0].id
    response = client.delete(f"/api/assignments/{assignment_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

# Error cases
def test_get_nonexistent_child(client):
    response = client.get("/api/children/999")
    assert response.status_code == 404

def test_complete_nonexistent_assignment(client):
    response = client.put("/api/assignments/999/complete")
    assert response.status_code == 404

def test_assign_chores_to_nonexistent_child(client):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    response = client.post(
        "/api/weekly-assignments/",
        json={
            "child_id": 999,  # Non-existent ID
            "chore_ids": [1, 2, 3],
            "week_start": week_start.isoformat()
        }
    )
    assert response.status_code == 404

def test_delete_nonexistent_assignment(client):
    response = client.delete("/api/assignments/999")
    assert response.status_code == 404

# Integration tests
def test_full_workflow(client):
    # 1. Create a child
    child_response = client.post(
        "/api/children/",
        json={"name": "David", "weekly_allowance": 10.0}
    )
    assert child_response.status_code == 200
    child_id = child_response.json()["id"]

    # 2. Create some chores
    chore_ids = []
    for chore_data in [
        {"name": "Study", "description": "Do homework"},
        {"name": "Exercise", "description": "30 minutes activity"}
    ]:
        chore_response = client.post("/api/chores/", json=chore_data)
        assert chore_response.status_code == 200
        chore_ids.append(chore_response.json()["id"])

    # 3. Assign chores to child
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    assign_response = client.post(
        "/api/weekly-assignments/",
        json={
            "child_id": child_id,
            "chore_ids": chore_ids,
            "week_start": week_start.isoformat()
        }
    )
    assert assign_response.status_code == 200
    assignments = assign_response.json()
    assert len(assignments) == len(chore_ids)

    # 4. Complete an assignment
    assignment_id = assignments[0]["id"]
    complete_response = client.put(f"/api/assignments/{assignment_id}/complete")
    assert complete_response.status_code == 200

    # 5. Check assignment history
    history_response = client.get(f"/api/assignments/history/{child_id}")
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) > 0
    completed_assignment = next(
        (a for a in history if a["id"] == assignment_id), None
    )
    assert completed_assignment["is_completed"] == True