"""Tests for Google Workspace document inspection and title semantics."""

import pytest
from neatworkspace.docs_inspector import is_generic_title, classify_cloud_item
from neatworkspace.config import MIME_DOCUMENT, MIME_SPREADSHEET, MIME_PRESENTATION


def test_generic_title_detection():
    assert is_generic_title("Untitled document") is True
    assert is_generic_title("Untitled spreadsheet") is True
    assert is_generic_title("Untitled presentation (1)") is True
    assert is_generic_title("Copy of Q3 Budget") is True
    assert is_generic_title("New Document") is True
    assert is_generic_title("Document 1") is True

    # Real titles should not be marked generic
    assert is_generic_title("Q3 Financial Forecast 2026") is False
    assert is_generic_title("Resume - Jane Doe") is False
    assert is_generic_title("Meeting Notes 2026-10-25") is False


def test_classify_native_google_apps():
    cat, _ = classify_cloud_item("Data Analysis", MIME_SPREADSHEET)
    assert cat == "Spreadsheets & Data"

    cat, _ = classify_cloud_item("Pitch Deck", MIME_PRESENTATION)
    assert cat == "Presentations & Decks"


def test_classify_semantic_documents():
    cat, _ = classify_cloud_item("Employment_Contract_NDA.pdf", "application/pdf")
    assert cat == "Documents/Legal & Contracts"

    cat, _ = classify_cloud_item("Invoice_Oct_2026.pdf", "application/pdf")
    assert cat == "Documents/Finance & Invoices"

    cat, _ = classify_cloud_item("Machine_Learning_Course_Syllabus.docx", "application/vnd.openxmlformats")
    assert cat == "Documents/Academic & Education"

    cat, _ = classify_cloud_item("Software_Engineer_Resume.pdf", "application/pdf")
    assert cat == "Documents/Career & Resumes"
