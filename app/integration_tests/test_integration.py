import pytest
import requests
import time
import os
from datetime import datetime
from urllib.parse import urljoin
import logging
from app.integration_tests.cleanup_registry import CleanupRegistry

logging.basicConfig(level=logging.INFO)

class APIClient:
    def __init__(self):
        self.base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.timeout = 30

    def _url(self, path):
        return urljoin(self.base_url, path)

    def wait_for_api(self, max_retries=30, delay=1):
        for _ in range(max_retries):
            try:
                response = requests.get(self._url('/health'))
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass
            time.sleep(delay)
        raise Exception("API failed to become available")

    def post(self, path, json=None):
        return requests.post(self._url(path), json=json, timeout=self.timeout)

    def get(self, path):
        return requests.get(self._url(path), timeout=self.timeout)

    def put(self, path):
        return requests.put(self._url(path), timeout=self.timeout)

    def delete(self, path):
        return requests.delete(self._url(path), timeout=self.timeout)

@pytest.fixture(scope="session")
def api_client():
    client = APIClient()
    client.wait_for_api()
    return client

@pytest.fixture(scope="function")
def cleanup_registry(api_client):  # Add api_client as a parameter
    registry = CleanupRegistry()
    yield registry
    registry.cleanup(api_client)  # Now using the injected api_client

# app/integration_tests/test_integration.py
def test_full_chores_workflow(api_client, cleanup_registry):
    # Create a child
    child_data = {
        "name": f"Test Child {datetime.now().isoformat()}",
        "weekly_allowance": 10.0
    }
    child_response = api_client.post('/api/children/', json=child_data)
    assert child_response.status_code == 200
    child = child_response.json()
    child_id = child['id']
    cleanup_registry.register_child(child_id)

    # Create chores with frequencies
    chore_ids = []
    chores = [
        {"name": "Test Chore 1", "description": "Description 1", "frequency_per_week": 3},
        {"name": "Test Chore 2", "description": "Description 2", "frequency_per_week": 2}
    ]
    
    for chore in chores:
        response = api_client.post('/api/chores/', json=chore)
        assert response.status_code == 200
        chore_id = response.json()['id']
        chore_ids.append(chore_id)
        cleanup_registry.register_chore(chore_id)

    # Assign weekly chores
    week_start = datetime.now().date().isoformat()
    assign_response = api_client.post(
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
        complete_response = api_client.put(f'/api/assignments/{assignment["id"]}/complete')
        assert complete_response.status_code == 200

    # Verify assignment history
    history_response = api_client.get(f'/api/assignments/history/{child_id}')
    assert history_response.status_code == 200
    history = history_response.json()
    
    completed_assignments = [a for a in history if a["is_completed"]]
    assert len(completed_assignments) == 3

    # Verify occurrence numbers are correct
    chore1_assignments = [a for a in assignments if a["chore_id"] == chore_ids[0]]
    chore2_assignments = [a for a in assignments if a["chore_id"] == chore_ids[1]]
    assert len(chore1_assignments) == 3
    assert len(chore2_assignments) == 2
    assert {a["occurrence_number"] for a in chore1_assignments} == {1, 2, 3}
    assert {a["occurrence_number"] for a in chore2_assignments} == {1, 2}
    
def test_error_handling(api_client):
    """Test API error responses"""
    
    # Test nonexistent child
    response = api_client.get('/api/children/99999')
    assert response.status_code == 404

    # Test invalid chore assignment
    week_start = datetime.now().date().isoformat()
    response = api_client.post(
    '/api/weekly-assignments/',
    json={
        "child_id": 99999,
        "chore_ids": [1, 2, 3],
        "week_start": week_start
    }
    )
    assert response.status_code == 404

def test_concurrent_assignments(api_client, cleanup_registry):
    # Create a child
    child_response = api_client.post('/api/children/', 
        json={"name": "Concurrent Test Child", "weekly_allowance": 15.0}
    )
    child_id = child_response.json()['id']
    cleanup_registry.register_child(child_id)  # Register child

    # Create multiple chores
    chore_ids = []
    for i in range(5):
        chore_response = api_client.post('/api/chores/', 
            json={
                "name": f"Concurrent Chore {i}",
                "description": f"Description {i}",
                "points": i + 1
            }
        )
        chore_id = chore_response.json()['id']
        chore_ids.append(chore_id)
        cleanup_registry.register_chore(chore_id)  # Register each chore

    # Assign all chores at once
    week_start = datetime.now().date().isoformat()
    assign_response = api_client.post(
        '/api/weekly-assignments/',
        json={
            "child_id": child_id,
            "chore_ids": chore_ids,
            "week_start": week_start
        }
    )
    
    assert assign_response.status_code == 200
    assignments = assign_response.json()
    for assignment in assignments:
        cleanup_registry.register_assignment(assignment['id'])  # Register each assignment

def test_weekly_boundaries(api_client, cleanup_registry):
    # Create a child
    child_response = api_client.post('/api/children/', 
        json={"name": "Weekly Test Child", "weekly_allowance": 20.0}
    )
    child_id = child_response.json()['id']
    cleanup_registry.register_child(child_id)  # Register child

    # Create a chore
    chore_response = api_client.post('/api/chores/', 
        json={
            "name": "Weekly Chore",
            "description": "Weekly test chore",
            "points": 5
        }
    )
    chore_id = chore_response.json()['id']
    cleanup_registry.register_chore(chore_id)  # Register chore

    # Assign chore
    week_start = datetime.now().date().isoformat()
    assign_response = api_client.post(
        '/api/weekly-assignments/',
        json={
            "child_id": child_id,
            "chore_ids": [chore_id],
            "week_start": week_start
        }
    )
    
    for assignment in assign_response.json():
        cleanup_registry.register_assignment(assignment['id'])  # Register assignments
