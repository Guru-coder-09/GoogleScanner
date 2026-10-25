"""Tests for Google Drive organization planning and mock cloud moves."""

import pytest
from neatworkspace.drive_scanner import DriveItem
from neatworkspace.drive_organizer import DriveOrganizer, CloudPlanItem


def test_drive_organizer_build_plan_with_duplicates():
    f1 = DriveItem(id="1", name="Resume.pdf", mime_type="application/pdf", parents=["root"])
    f2 = DriveItem(id="2", name="Resume (1).pdf", mime_type="application/pdf", parents=["root"])

    dup_map = {
        "2": {"duplicate": f2, "master": f1, "hash": "hash123"}
    }

    organizer = DriveOrganizer(drive_service=None)
    plan = organizer.build_plan([f1, f2], duplicate_map=dup_map)

    assert len(plan) == 2
    assert plan[0].target_category == "Documents/Career & Resumes"
    assert plan[0].is_duplicate is False

    assert plan[1].target_category == "_Duplicates"
    assert plan[1].is_duplicate is True
    assert plan[1].master_name == "Resume.pdf"
