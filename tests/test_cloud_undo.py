"""Tests for Google Drive transactional journal and undo rollback."""

import pytest
from pathlib import Path
from neatworkspace.journal import CloudJournal
from neatworkspace.drive_organizer import DriveOrganizer


class MockDriveMoveService:
    def __init__(self):
        self.moves = []

    def files(self):
        return self

    def update(self, fileId, addParents, removeParents, **kwargs):
        self.moves.append({
            "fileId": fileId,
            "addParents": addParents,
            "removeParents": removeParents
        })
        return self

    def execute(self):
        return {}


def test_cloud_journal_record_and_rollback(tmp_path: Path):
    db_file = tmp_path / "cloud_journal.json"
    journal = CloudJournal(db_path=db_file)

    session_id = "test_sess_001"
    moves = [
        {
            "file_id": "file_abc",
            "file_name": "Contract.pdf",
            "original_parent_ids": ["root"],
            "destination_folder_id": "folder_legal",
            "category": "Documents/Legal & Contracts"
        }
    ]

    journal.record_session(session_id, moves, [])
    assert len(journal.list_sessions()) == 1

    last = journal.get_last_session()
    assert last["session_id"] == session_id
    assert last["status"] == "completed"

    mock_service = MockDriveMoveService()
    organizer = DriveOrganizer(drive_service=mock_service, journal=journal)

    # Rollback session
    res = organizer.rollback_session(session_id)
    assert res["success"] is True
    assert res["restored_count"] == 1
    assert res["failed_count"] == 0

    # Verify API called to swap parents back
    assert len(mock_service.moves) == 1
    assert mock_service.moves[0]["fileId"] == "file_abc"
    assert mock_service.moves[0]["addParents"] == "root"
    assert mock_service.moves[0]["removeParents"] == "folder_legal"

    # Journal marked undone
    updated_session = journal.get_session(session_id)
    assert updated_session["status"] == "undone"
