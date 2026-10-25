"""Configuration, cloud taxonomies, and OAuth security scopes for NeatWorkspace."""

import os
from pathlib import Path
from typing import List, Dict, Set

# App Data Directory for user tokens and audit journals
USER_HOME = Path.home()
APP_DATA_DIR = USER_HOME / ".neatworkspace"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Credentials & OAuth Tokens
DEFAULT_CREDENTIALS_PATH = Path("credentials.json")
ALT_CREDENTIALS_PATH = APP_DATA_DIR / "credentials.json"
TOKEN_STORAGE_PATH = APP_DATA_DIR / "token.json"
HISTORY_JOURNAL_PATH = APP_DATA_DIR / "history.json"

# Minimal required OAuth 2.0 Scopes for Drive & Photos
# Drive: Full drive scope enables managing folder parents, moving files, and creating organized folders
# Photos: Read media metadata and create/append to organized albums
OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/photoslibrary.readonly",
    "https://www.googleapis.com/auth/photoslibrary.appendonly"
]

# Google Workspace MIME Types
MIME_FOLDER = "application/vnd.google-apps.folder"
MIME_DOCUMENT = "application/vnd.google-apps.document"
MIME_SPREADSHEET = "application/vnd.google-apps.spreadsheet"
MIME_PRESENTATION = "application/vnd.google-apps.presentation"
MIME_FORM = "application/vnd.google-apps.form"
MIME_SHORTCUT = "application/vnd.google-apps.shortcut"

# Standard File Extension Mappings for Non-native Drive Files
EXTENSION_CATEGORIES: Dict[str, str] = {
    # Documents
    ".pdf": "Documents/General",
    ".docx": "Documents/General",
    ".doc": "Documents/General",
    ".txt": "Documents/General",
    ".rtf": "Documents/General",
    ".md": "Documents/General",

    # Spreadsheets
    ".xlsx": "Spreadsheets & Data",
    ".xls": "Spreadsheets & Data",
    ".csv": "Spreadsheets & Data",
    ".tsv": "Spreadsheets & Data",

    # Presentations
    ".pptx": "Presentations & Decks",
    ".ppt": "Presentations & Decks",
    ".key": "Presentations & Decks",

    # Media
    ".png": "Media & Recordings/Images",
    ".jpg": "Media & Recordings/Images",
    ".jpeg": "Media & Recordings/Images",
    ".webp": "Media & Recordings/Images",
    ".mp4": "Media & Recordings/Videos",
    ".mov": "Media & Recordings/Videos",
    ".mp3": "Media & Recordings/Audio",
    ".wav": "Media & Recordings/Audio",

    # Archives & Code
    ".zip": "Archives & Backups",
    ".rar": "Archives & Backups",
    ".tar": "Archives & Backups",
    ".gz": "Archives & Backups",
    ".py": "Projects & Code/Scripts",
    ".js": "Projects & Code/Scripts",
    ".html": "Projects & Code/Web",
    ".json": "Projects & Code/Data"
}

# Protected folder names that must NEVER be touched or moved
PROTECTED_FOLDER_NAMES: Set[str] = {
    "root",
    "_duplicates",
    "backup",
    "backups",
    "google photos",
    "shared with me"
}
