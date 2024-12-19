# app/integration_tests/test_integration.py
import pytest
from datetime import datetime, date, timedelta

def test_full_chores_workflow(auth_client, test_user):
    # Create a child
    child_data = {
        "name": f"Test Child {datetime.now().isoformat()}",
        "weekly_allowance": 10.0
    }
    child_response = auth_client.post('/api/children/', json=child_data)
    assert child_response.status_code == 200
    child = child_response.json()
    child_id = child['id']

    # Create chores with frequencies
    chore_ids = []
    chores = [
        {
            "name": "Test Chore 1", 
            "description": "Description 1", 
            "frequency_per_week": 3
        },
        {
            "name": "Test Chore 2", 
            "description": "Description 2", 
            "frequency_per_week": 2
        }
    ]
    
    for chore in chores:
        response = auth_client.post('/api/chores/', json=chore)
        assert response.status_code == 200
        chore_id = response.json()['id']
        chore_ids.append(chore_id)

    # Assign weekly chores
    week_start = datetime.now().date().isoformat()
    assign_response = auth_client.post(
        '/api/weekly-assignments/',
        json={
            "child_id": child_id,
            "chore_ids": chore_ids,
            "week_start": week_start
        }
    )
    
    assert assign_response.status_code == 200
    assignments = assign_response.json()
    # Should have 5 total assignments (3 for first chore + 2 for second chore)
    assert len(assignments) == 5

    # Complete some assignments
    for assignment in assignments[:3]:
        complete_response = auth_client.put(f'/api/assignments/{assignment["id"]}/complete')
        assert complete_response.status_code == 200
        completed = complete_response.json()
        assert completed["is_completed"] is True
        assert completed["completion_date"] is not None

    # Verify weekly assignments
    weekly_response = auth_client.get(
        f'/api/weekly-assignments/{child_id}',
        params={"week_start": week_start}
    )
    assert weekly_response.status_code == 200
    weekly_assignments = weekly_response.json()
    assert len(weekly_assignments) == 5

def test_error_handling(auth_client):
    """Test API error responses"""
    response = auth_client.get('/api/children/99999')
    assert response.status_code == 404

def test_unauthenticated_access(client):
    """Test that unauthenticated requests are rejected"""
    endpoints = [
        "/api/children/",
        "/api/chores/",
        f"/api/weekly-assignments/1"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"

def test_invalid_token(client):
    """Test that invalid tokens are rejected"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/children/", headers=headers)
    assert response.status_code == 401