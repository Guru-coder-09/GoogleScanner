# ✨ GoogleScanner: Intelligent Google Workspace & Cloud Photos Automation

[![CI Test Suite](https://github.com/Guru-coder-09/GoogleScanner/actions/workflows/ci.yml/badge.svg)](https://github.com/Guru-coder-09/GoogleScanner/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests: 11 Passed](https://img.shields.io/badge/tests-11%20passed-brightgreen.svg)](https://github.com/Guru-coder-09/GoogleScanner/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**GoogleScanner** is a privacy-first, zero-data-loss automation workstation for **Google Drive, Google Docs, Sheets, Slides, and Google Photos**. It eliminates root drive chaos, isolates exact duplicate cloud files via native MD5 checksums, cleans up generic "Untitled" documents, clusters Google Photos into chronological albums, and provides a **100% reversible cloud rollback engine**.

---

## 🌟 Core Features

| Feature | Description |
| :--- | :--- |
| **📁 Google Drive Root Declutter** | Organizes scattered cloud files into an intuitive universal taxonomy (`Documents/`, `Spreadsheets & Data/`, `Presentations & Decks/`, `Archives & Backups/`). |
| **⚠️ Native MD5 Cloud Deduplication** | Uses Google Drive's native MD5 checksums to detect exact duplicate cloud uploads, isolating redundant copies to `_Duplicates/` while keeping the original master file intact. |
| **📄 Generic & "Untitled Document" Audit** | Detects default, uninformative titles (`Untitled document`, `Untitled spreadsheet`, `Copy of...`) so you can clean up cloud bloat. |
| **📸 Google Photos Chronological Albums** | Clusters photos and videos into structured Year/Month albums (e.g. `NeatPhotos 2026 10-October`) using embedded EXIF capture timestamps. |
| **🔍 Rapid Burst & Screenshot Sorter** | Identifies rapid burst sequences (photos taken <2 seconds apart with identical resolutions) to help reclaim storage quota. |
| **🛡️ 100% Reversible Cloud Rollback (`--undo`)** | Every file move is recorded in a local transaction journal at `~/.neatworkspace/history.json`. Run `python main.py --undo` anytime to restore files to their original parent folders. |
| **🔒 Zero-Destruction Safety Policy** | NeatWorkspace **never calls permanent delete**. Files can only be moved or quarantined; your cloud storage is always safe. |

---

## 🌐 Google Drive Taxonomy

```text
Google Drive Root/
├── _Duplicates/                 (Quarantined identical cloud file copies)
├── Documents/
│   ├── Legal & Contracts/       (NDAs, MOUs, Court filings, Regulatory notices)
│   ├── Finance & Invoices/      (Receipts, Bills, Tax statements, Expenses)
│   ├── Academic & Education/    (Course guides, Syllabi, Lab handbooks)
│   ├── Career & Resumes/        (Resumes, CVs, Portfolios, Offer letters)
│   ├── Work & Reports/          (Meeting minutes, Tech specs, Proposals)
│   └── General/                 (General Google Docs & documents)
├── Spreadsheets & Data/         (Google Sheets, Excel files, CSV datasets)
├── Presentations & Decks/       (Google Slides, Pitch decks, Keynote files)
├── Forms & Surveys/             (Google Forms)
├── Media & Recordings/          (Images, Videos, Audio recordings)
└── Archives & Backups/          (Zip files, tarballs, data backups)
```

---

## 🚀 Quickstart & Setup

### 1. Installation

```bash
git clone https://github.com/Guru-coder-09/GoogleScanner.git
cd GoogleScanner

# Setup virtual environment
python -m venv .venv

# Activate:
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (Command Prompt):
.venv\Scripts\activate.bat
# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Google OAuth 2.0 Credentials (One-Time Setup)

To allow NeatWorkspace to access your Google Drive & Photos securely:

1. Visit the **[Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials)**.
2. Click **Create Project** (e.g. `NeatWorkspace`).
3. Enable the **Google Drive API** and **Google Photos Library API** under **APIs & Services > Library**.
4. In **OAuth consent screen**, select **External**, enter an app name (`NeatWorkspace`), and add your own email under **Test Users**.
5. Go to **Credentials > + Create Credentials > OAuth client ID**:
   - Choose **Desktop App**.
   - Download the JSON file and save it as **`credentials.json`** in the `NeatWorkspace` project folder.

---

## 💻 Command Line Usage

```bash
# Preview Google Drive organization without moving any files (Simulation Mode)
python main.py --drive --sim

# Organize Google Drive root into clean categories
python main.py --drive

# Scan for exact duplicate cloud files via MD5 checksums
python main.py --duplicates --sim

# Cluster Google Photos into chronological Year/Month albums
python main.py --photos --sim

# 1-Click Rollback: Restore all cloud files to original parent folders
python main.py --undo

# Auto-confirm without interactive prompt
python main.py --drive -y
```

---

## 🛡️ Security & Privacy Architecture

* **Least-Privilege Scopes**: Requests only the necessary scopes to organize your personal files.
* **Token Protection**: Credentials (`credentials.json`) and access tokens (`token.json`) are stored strictly on your local machine and blocked in `.gitignore`. They are **never committed or transmitted anywhere**.
* **Zero Permanent Deletion**: NeatWorkspace does not issue destructive purge calls. Any duplicate isolation moves files to `_Duplicates/` folder.
* **Full Reversibility**: Changes to parent folder references are journaled in `~/.neatworkspace/history.json` and restored with `python main.py --undo`.

---

## 🧪 Automated Testing

NeatWorkspace includes an automated test suite executed on every commit across **Ubuntu & Windows** using GitHub Actions:

```bash
pytest -v
```

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
