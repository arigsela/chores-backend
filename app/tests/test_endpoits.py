# app/tests/test_endpoints.py
from fastapi.testclient import TestClient
from datetime import date, timedelta
import pytest

def test_create_child(authenticated_client):
    response = authenticated_client.post(
        "/api/children/",
        json={"name": "Charlie", "weekly_allowance": 12.0}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Charlie"
    assert data["weekly_allowance"] == 12.0
    assert "id" in data

def test_get_children(authenticated_client, sample_data):
    response = authenticated_client.get("/api/children/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(child["name"] == "Alice" for child in data)
    assert any(child["name"] == "Bob" for child in data)

def test_create_chore(authenticated_client):
    response = authenticated_client.post(
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

def test_create_chore_default_frequency(authenticated_client):
    """Test that chores default to frequency of 1 if not specified"""
    response = authenticated_client.post(
        "/api/chores/",
        json={
            "name": "Clean Garage",
            "description": "Sweep and organize garage"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["frequency_per_week"] == 1

def test_invalid_frequency(authenticated_client):
    """Test that frequency must be positive"""
    response = authenticated_client.post(
        "/api/chores/",
        json={
            "name": "Test Chore",
            "description": "Test Description",
            "frequency_per_week": 0  # Invalid frequency
        }
    )
    assert response.status_code == 422  # Validation error

def test_get_chores(authenticated_client, sample_data):
    response = authenticated_client.get("/api/chores/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert any(chore["name"] == "Clean Room" for chore in data)

def test_get_weekly_assignments(authenticated_client, sample_data):
    """Test getting weekly assignments"""
    child_id = sample_data["children"]["alice"].id
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    response = authenticated_client.get(
        f"/api/weekly-assignments/{child_id}",
        params={"week_start": week_start.isoformat()}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assignment = data[0]
        assert "child_id" in assignment
        assert "chore" in assignment
        assert "week_start" in assignment

def test_weekly_assignments_create_with_frequency(authenticated_client, sample_data):
    """Test that assignments are created according to chore frequency"""
    child_id = sample_data["children"]["alice"].id
    
    # Create a chore with frequency > 1
    chore_data = {
        "name": "Daily Exercise",
        "description": "30 minutes of exercise",
        "frequency_per_week": 5
    }
    chore_response = authenticated_client.post("/api/chores/", json=chore_data)
    assert chore_response.status_code == 200
    chore = chore_response.json()
    
    # Assign the chore
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    assign_response = authenticated_client.post(
        "/api/weekly-assignments/",
        json={
            "child_id": child_id,
            "chore_ids": [chore["id"]],
            "week_start": week_start.isoformat()
        }
    )
    
    assert assign_response.status_code == 200
    assignments = assign_response.json()
    
    # Should have 5 assignments (frequency_per_week = 5)
    assert len(assignments) == 5
    
    # Check occurrence numbers
    occurrence_numbers = {a["occurrence_number"] for a in assignments}
    assert occurrence_numbers == {1, 2, 3, 4, 5}

def test_complete_assignment(authenticated_client, sample_data):
    """Test completing an assignment"""
    assignment_id = sample_data["assignments"][0].id
    response = authenticated_client.put(f"/api/assignments/{assignment_id}/complete")
    assert response.status_code == 200
    data = response.json()
    assert data["is_completed"] is True
    assert "completion_date" in data

def test_get_nonexistent_weekly_assignments(authenticated_client):
    """Test getting assignments for nonexistent child/week"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    response = authenticated_client.get(
        "/api/weekly-assignments/99999",
        params={"week_start": week_start.isoformat()}
    )
    assert response.status_code == 404

def test_complete_assignment_with_date(authenticated_client, sample_data):
    """Test completing an assignment sets completion date"""
    assignment_id = sample_data["assignments"][0].id
    response = authenticated_client.put(f"/api/assignments/{assignment_id}/complete")
    assert response.status_code == 200
    
    data = response.json()
    assert data["is_completed"] is True
    assert "completion_date" in data
    assert data["completion_date"] is not None

def test_weekly_assignment_filtering(authenticated_client, sample_data):
    """Test that assignments are properly filtered by week"""
    child_id = sample_data["children"]["alice"].id
    
    # Get assignments for current week
    today = date.today()
    current_week = today - timedelta(days=today.weekday())
    current_response = authenticated_client.get(
        f"/api/weekly-assignments/{child_id}",
        params={"week_start": current_week.isoformat()}
    )
    assert current_response.status_code == 200
    
    # Get assignments for next week
    next_week = current_week + timedelta(days=7)
    next_response = authenticated_client.get(
        f"/api/weekly-assignments/{child_id}",
        params={"week_start": next_week.isoformat()}
    )
    assert next_response.status_code == 200
    
    # Assignments should be different
    current_assignments = current_response.json()
    next_assignments = next_response.json()
    assert len(next_assignments) == 0  # Should be no assignments for next week

def test_error_handling(authenticated_client):
    """Test API error responses"""
    response = authenticated_client.get("/api/children/99999")
    assert response.status_code == 404

def test_assign_chores_to_nonexistent_child(authenticated_client):
    """Test assigning chores to nonexistent child"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    response = authenticated_client.post(
        "/api/weekly-assignments/",
        json={
            "child_id": 99999,
            "chore_ids": [1, 2, 3],
            "week_start": week_start.isoformat()
        }
    )
    assert response.status_code == 404

def test_invalid_token(client):
    """Test that invalid tokens are rejected"""
    headers = {"Authorization": "Bearer invalid_token"}
    endpoints = [
        "/api/children/",
        "/api/chores/",
        f"/api/weekly-assignments/1"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint, headers=headers)
        assert response.status_code == 401, f"Endpoint {endpoint} should reject invalid token"

def test_full_workflow(authenticated_client):
    """Test the complete chore assignment workflow"""
    # 1. Create a child
    child_response = authenticated_client.post(
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
        chore_response = authenticated_client.post("/api/chores/", json=chore_data)
        assert chore_response.status_code == 200
        chore_ids.append(chore_response.json()["id"])

    # 3. Assign chores to child
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    assign_response = authenticated_client.post(
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

    # 4. Complete some assignments and verify completion
    for assignment in assignments[:3]:
        complete_response = authenticated_client.put(f'/api/assignments/{assignment["id"]}/complete')
        assert complete_response.status_code == 200
        completed_assignment = complete_response.json()
        assert completed_assignment["is_completed"] is True
        assert completed_assignment["completion_date"] is not None

    # 5. Verify assignments were properly created
    get_response = authenticated_client.get(
        f"/api/weekly-assignments/{child_id}",
        params={"week_start": week_start.isoformat()}
    )
    assert get_response.status_code == 200
    all_assignments = get_response.json()
    assert len(all_assignments) == 8

    # Verify study assignments
    study_assignments = [a for a in all_assignments if a["chore"]["name"] == "Study"]
    exercise_assignments = [a for a in all_assignments if a["chore"]["name"] == "Exercise"]
    assert len(study_assignments) == 5
    assert len(exercise_assignments) == 3

    # Verify occurrence numbers
    study_occurrences = {a["occurrence_number"] for a in study_assignments}
    exercise_occurrences = {a["occurrence_number"] for a in exercise_assignments}
    assert study_occurrences == {1, 2, 3, 4, 5}
    assert exercise_occurrences == {1, 2, 3}