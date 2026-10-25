"""Tests for Google Drive item parsing and native MD5 deduplication."""

import pytest
from neatworkspace.drive_scanner import DriveScanner, DriveItem
from neatworkspace.config import MIME_FOLDER


class MockFilesResource:
    def __init__(self, file_list):
        self._list = file_list

    def list(self, **kwargs):
        return self

    def execute(self):
        return {"files": self._list}


class MockDriveService:
    def __init__(self, file_list):
        self._files = MockFilesResource(file_list)

    def files(self):
        return self._files


def test_drive_scanner_fetch_and_parse():
    mock_files = [
        {
            "id": "1",
            "name": "Untitled document",
            "mimeType": "application/vnd.google-apps.document",
            "parents": ["root"]
        },
        {
            "id": "2",
            "name": "Invoice.pdf",
            "mimeType": "application/pdf",
            "parents": ["root"],
            "size": "1048576",
            "md5Checksum": "abc123md5"
        }
    ]
    service = MockDriveService(mock_files)
    scanner = DriveScanner(service)
    items = scanner.fetch_items()

    assert len(items) == 2
    assert items[0].is_generic is True
    assert items[1].md5_checksum == "abc123md5"
    assert items[1].size == 1048576


def test_drive_scanner_identify_duplicates():
    f1 = DriveItem(id="1", name="Budget.xlsx", mime_type="application/vnd.ms-excel", parents=["root"], md5_checksum="hash1")
    f2 = DriveItem(id="2", name="Copy of Budget.xlsx", mime_type="application/vnd.ms-excel", parents=["root"], md5_checksum="hash1")
    f3 = DriveItem(id="3", name="Budget (1).xlsx", mime_type="application/vnd.ms-excel", parents=["root"], md5_checksum="hash1")
    f4 = DriveItem(id="4", name="Unique.pdf", mime_type="application/pdf", parents=["root"], md5_checksum="hash2")

    scanner = DriveScanner(MockDriveService([]))
    dups = scanner.identify_duplicates([f1, f2, f3, f4])

    assert len(dups) == 2
    # f1 has cleanest name, so f2 and f3 should be marked duplicates of f1
    assert "2" in dups
    assert "3" in dups
    assert dups["2"]["master"].name == "Budget.xlsx"
    assert dups["3"]["master"].name == "Budget.xlsx"
    assert "4" not in dups
