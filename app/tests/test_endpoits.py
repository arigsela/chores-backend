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
            "description": "Feed the pet and refresh water",
            "frequency_per_week": 7
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Feed Pet"
    assert data["frequency_per_week"] == 7
    
def test_create_chore_default_frequency(client):
    """Test that chores default to frequency of 1 if not specified"""
    response = client.post(
        "/api/chores/",
        json={
            "name": "Clean Garage",
            "description": "Sweep and organize garage"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["frequency_per_week"] == 1

def test_invalid_frequency(client):
    """Test that frequency must be positive"""
    response = client.post(
        "/api/chores/",
        json={
            "name": "Test Chore",
            "description": "Test Description",
            "frequency_per_week": 0  # Invalid frequency
        }
    )
    assert response.status_code == 422  # Validation error

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

# Update integration tests
def test_full_workflow(client):
    # 1. Create a child
    child_response = client.post(
        "/api/children/",
        json={"name": "David", "weekly_allowance": 10.0}
    )
    assert child_response.status_code == 200
    child_id = child_response.json()["id"]

    # 2. Create chores with different frequencies
    chore_ids = []
    for chore_data in [
        {"name": "Study", "description": "Do homework", "frequency_per_week": 5},
        {"name": "Exercise", "description": "30 minutes activity", "frequency_per_week": 3}
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
    
    # Should have 8 total assignments (5 for study + 3 for exercise)
    assert len(assignments) == 8

    # Verify multiple occurrences
    study_assignments = [a for a in assignments if a["chore"]["name"] == "Study"]
    exercise_assignments = [a for a in assignments if a["chore"]["name"] == "Exercise"]
    assert len(study_assignments) == 5
    assert len(exercise_assignments) == 3

    # 4. Complete some assignments
    for assignment in assignments[:3]:  # Complete first 3 assignments
        complete_response = client.put(f'/api/assignments/{assignment["id"]}/complete')
        assert complete_response.status_code == 200

    # 5. Check assignment history
    history_response = client.get(f'/api/assignments/history/{child_id}')
    assert history_response.status_code == 200
    history = history_response.json()
    
    # Verify completed assignments
    completed_count = sum(1 for a in history if a["is_completed"])
    assert completed_count == 3

    # Verify occurrence numbers
    study_occurrences = {a["occurrence_number"] for a in study_assignments}
    exercise_occurrences = {a["occurrence_number"] for a in exercise_assignments}
    assert study_occurrences == set(range(1, 6))  # 1-5
    assert exercise_occurrences == set(range(1, 4))  # 1-3