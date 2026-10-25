"""Semantic classification and title inspection for Google Workspace documents."""

import re
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

from .config import (
    MIME_DOCUMENT,
    MIME_SPREADSHEET,
    MIME_PRESENTATION,
    MIME_FORM,
    EXTENSION_CATEGORIES
)

GENERIC_DOCUMENT_PATTERNS = [
    r"^untitled\s*(document|spreadsheet|presentation|form)?(?:\s*\(\d+\))?$",
    r"^copy\s+of\s+.*",
    r"^new\s+document(?:\s*\(\d+\))?$",
    r"^document\s*\d*$",
    r"^doc\s*\d*$",
    r"^presentation\s*\d*$"
]


def is_generic_title(title: str) -> bool:
    """Determine if a Google Doc/Sheet/Slide title is generic, default, or uninformative."""
    lower_title = title.strip().lower()
    for pattern in GENERIC_DOCUMENT_PATTERNS:
        if re.match(pattern, lower_title):
            return True
    return False


def classify_cloud_item(name: str, mime_type: str, file_size: Optional[int] = None) -> Tuple[str, str]:
    """
    Classify a Google Drive file into structured universal folders.
    Returns: (category_folder_path, classification_reason)
    """
    lower = name.lower()

    # 1. Native Google Workspace Apps
    if mime_type == MIME_SPREADSHEET:
        return "Spreadsheets & Data", "Google Sheets spreadsheet"

    if mime_type == MIME_PRESENTATION:
        return "Presentations & Decks", "Google Slides presentation"

    if mime_type == MIME_FORM:
        return "Forms & Surveys", "Google Form"

    # 2. Document Semantics (Google Docs, PDFs, Word Docs)
    # Legal
    if any(w in lower for w in ["court", "affidavit", "petition", "notice", "mou", "agreement", "nda", "contract"]):
        return "Documents/Legal & Contracts", "Legal agreement or official filing"

    # Finance
    if any(w in lower for w in ["invoice", "receipt", "bill", "salary", "statement", "tax", "itr", "challan", "expense"]):
        return "Documents/Finance & Invoices", "Invoice, receipt or financial record"

    # Academic
    if any(w in lower for w in ["syllabus", "course", "curriculum", "handbook", "lab manual", "timetable", "roster", "exam"]):
        return "Documents/Academic & Education", "Course material or academic guide"

    # Career
    if any(w in lower for w in ["resume", "cv", "portfolio", "cover letter", "job description", "offer letter"]):
        return "Documents/Career & Resumes", "Professional resume or career document"

    # Work / Technical
    if any(w in lower for w in ["minutes", "meeting", "specs", "specification", "proposal", "brief", "architecture", "report"]):
        return "Documents/Work & Reports", "Project brief or technical report"

    if mime_type == MIME_DOCUMENT:
        return "Documents/General", "Google Docs document"

    # 3. Extension-based Classification for Non-native Files
    ext = Path(name).suffix.lower()
    if ext in EXTENSION_CATEGORIES:
        return EXTENSION_CATEGORIES[ext], f"File extension {ext}"

    return "Other Files", "Unclassified file"
