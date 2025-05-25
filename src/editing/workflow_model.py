# src/editing/workflow_model.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from .change_model import DocumentChange, ChangeStatus

class ChangeWorkflow(BaseModel):
    """
    Represents a workflow for managing a set of proposed changes to a document.
    """
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str  # type: ignore # Identifier for the document being updated
    proposed_changes: List[DocumentChange] = Field(default_factory=list)  # type: ignore # List of changes in this workflow
    created_at: datetime = Field(default_factory=datetime.utcnow)  # type: ignore
    updated_at: datetime = Field(default_factory=datetime.utcnow)  # type: ignore
    status: str = "active"  # type: ignore # e.g., "active", "completed", "cancelled"
    metadata: Dict[str, Any] = Field(default_factory=dict)  # type: ignore # Additional workflow-specific data

    def add_change(self, change: DocumentChange):
        """Adds a proposed change to the workflow.

        Args:
            change: The DocumentChange object to add.
        """
        self.proposed_changes.append(change)
        self.updated_at = datetime.utcnow()

    def get_change_by_id(self, change_id: str) -> Optional[DocumentChange]:
        """Retrieves a change by its ID within this workflow.

        Args:
            change_id: The ID of the change to retrieve.

        Returns:
            The DocumentChange object if found, otherwise None.
        """
        for change in self.proposed_changes:
            if change.change_id == change_id:
                return change
        return None

    def update_change_status(self, change_id: str, new_status: ChangeStatus):
        """Updates the status of a specific change within the workflow.

        Args:
            change_id: The ID of the change to update.
            new_status: The new status to assign to the change.

        Returns:
            True if the change was updated successfully, False otherwise.
        """
        change = self.get_change_by_id(change_id)
        if change:
            change.status = new_status
            self.updated_at = datetime.utcnow()
            return True
        return False

    def get_changes_by_status(self, status: ChangeStatus) -> List[DocumentChange]:
        """Returns a list of changes with a specific status.

        Args:
            status: The status to filter changes by.

        Returns:
            A list of DocumentChange objects with the specified status.
        """
        return [change for change in self.proposed_changes if change.status == status]

    def all_changes_reviewed(self) -> bool:
        """Checks if all proposed changes have been accepted or rejected.

        Returns:
            True if all changes have been reviewed, False otherwise.
        """
        return all(change.status in [ChangeStatus.ACCEPTED, ChangeStatus.REJECTED, ChangeStatus.APPLIED, ChangeStatus.FAILED] for change in self.proposed_changes)

    def get_accepted_changes(self) -> List[DocumentChange]:
        """Returns a list of changes that have been accepted.

        Returns:
            A list of DocumentChange objects that have been accepted.
        """
        return self.get_changes_by_status(ChangeStatus.ACCEPTED)

    def get_rejected_changes(self) -> List[DocumentChange]:
        """Returns a list of changes that have been rejected.

        Returns:
            A list of DocumentChange objects that have been rejected.
        """
        return self.get_changes_by_status(ChangeStatus.REJECTED)

    def get_proposed_changes(self) -> List[DocumentChange]:
        """Returns a list of changes that are still proposed.

        Returns:
            A list of DocumentChange objects that are still proposed.
        """
        return self.get_changes_by_status(ChangeStatus.PROPOSED)

# Example Usage (for illustration)
if __name__ == "__main__":
    from .change_model import ChangeType, LocationParagraph

    # Create some dummy changes
    change1 = DocumentChange(
        document_id="doc123",
        change_type=ChangeType.TEXT_UPDATE,
        location=LocationParagraph(paragraph_index=0),
        old_value="old text",
        new_value="new text",
        description="Update intro"
    )
    change2 = DocumentChange(
        document_id="doc123",
        change_type=ChangeType.PARAGRAPH_DELETE,
        location=LocationParagraph(paragraph_index=5),
        old_value="paragraph to delete",
        new_value=None,
        description="Remove redundant para"
    )
    change3 = DocumentChange(
        document_id="doc123",
        change_type=ChangeType.TEXT_UPDATE,
        location=LocationParagraph(paragraph_index=2),
        old_value="another old text",
        new_value="another new text",
        description="Update conclusion"
    )

    # Create a workflow
    workflow = ChangeWorkflow(document_id="doc123")
    workflow.add_change(change1)
    workflow.add_change(change2)
    workflow.add_change(change3)

    print(f"Initial workflow status: {workflow.status}")
    print(f"Total proposed changes: {len(workflow.proposed_changes)}")
    print(f"Proposed changes: {len(workflow.get_proposed_changes())}")

    # Accept one change
    workflow.update_change_status(change1.change_id, ChangeStatus.ACCEPTED)
    print(f"\nAfter accepting change 1:")
    change1_status = workflow.get_change_by_id(change1.change_id)
    if change1_status:
        print(f"Change 1 status: {change1_status.status}")
    else:
        print("Change 1 not found")
    print(f"Accepted changes: {len(workflow.get_accepted_changes())}")
    print(f"Proposed changes: {len(workflow.get_proposed_changes())}")

    # Reject another change
    workflow.update_change_status(change2.change_id, ChangeStatus.REJECTED)
    print(f"\nAfter rejecting change 2:")
    change2_status = workflow.get_change_by_id(change2.change_id)
    if change2_status:
        print(f"Change 2 status: {change2_status.status}")
    else:
        print("Change 2 not found")
    print(f"Rejected changes: {len(workflow.get_rejected_changes())}")
    print(f"Proposed changes: {len(workflow.get_proposed_changes())}")

    # Check if all reviewed
    print(f"\nAll changes reviewed: {workflow.all_changes_reviewed()}")

    # Accept the last change
    workflow.update_change_status(change3.change_id, ChangeStatus.ACCEPTED)
    print(f"\nAfter accepting change 3:")
    print(f"All changes reviewed: {workflow.all_changes_reviewed()}")

    print("\nWorkflow details:")
    print(workflow.model_dump_json(indent=2))