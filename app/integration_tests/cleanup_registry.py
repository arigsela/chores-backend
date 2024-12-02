# app/integration_tests/cleanup_registry.py
from typing import List
import logging

logger = logging.getLogger(__name__)

class CleanupRegistry:
    def __init__(self):
        self.children_ids: List[int] = []
        self.chore_ids: List[int] = []
        self.assignment_ids: List[int] = []

    def register_child(self, child_id: int):
        self.children_ids.append(child_id)

    def register_chore(self, chore_id: int):
        self.chore_ids.append(chore_id)

    def register_assignment(self, assignment_id: int):
        self.assignment_ids.append(assignment_id)

    def cleanup(self, api_client):
        """Clean up all registered resources in reverse order"""
        cleanup_errors = []

        # Clean assignments first
        for assignment_id in self.assignment_ids:
            try:
                logger.info(f"Cleaning up assignment {assignment_id}")
                response = api_client.delete(f'/api/assignments/{assignment_id}')
                if response.status_code not in (200, 404):  # 404 is ok - already deleted
                    cleanup_errors.append(f"Failed to delete assignment {assignment_id}")
            except Exception as e:
                cleanup_errors.append(f"Error deleting assignment {assignment_id}: {str(e)}")

        # Clean chores
        for chore_id in self.chore_ids:
            try:
                logger.info(f"Cleaning up chore {chore_id}")
                response = api_client.delete(f'/api/chores/{chore_id}')
                if response.status_code not in (200, 404):
                    cleanup_errors.append(f"Failed to delete chore {chore_id}")
            except Exception as e:
                cleanup_errors.append(f"Error deleting chore {chore_id}: {str(e)}")

        # Clean children last
        for child_id in self.children_ids:
            try:
                logger.info(f"Cleaning up child {child_id}")
                response = api_client.delete(f'/api/children/{child_id}')
                if response.status_code not in (200, 404):
                    cleanup_errors.append(f"Failed to delete child {child_id}")
            except Exception as e:
                cleanup_errors.append(f"Error deleting child {child_id}: {str(e)}")

        # Clear the registry
        self.children_ids.clear()
        self.chore_ids.clear()
        self.assignment_ids.clear()

        if cleanup_errors:
            logger.error("Cleanup errors occurred: %s", cleanup_errors)
            raise Exception("Cleanup failed: " + "; ".join(cleanup_errors))