"""FastAPI REST API server for GoogleScanner web UI."""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from .auth import AuthManager
from .drive_scanner import DriveScanner
from .drive_organizer import DriveOrganizer
from .photos_scanner import PhotosScanner
from .journal import CloudJournal

app = FastAPI(title="GoogleScanner API", version="1.0.0")

# Enable CORS so Lovable web app and local frontend can communicate seamlessly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth = AuthManager()


class MoveRequest(BaseModel):
    file_ids: Optional[List[str]] = None
    dry_run: bool = True
    folder_id: str = "root"


class UndoRequest(BaseModel):
    session_id: Optional[str] = None


def _format_bytes(b: int) -> str:
    if b >= 1024 ** 4:
        return f"{b / (1024 ** 4):.2f} TB"
    elif b >= 1024 ** 3:
        return f"{b / (1024 ** 3):.2f} GB"
    elif b >= 1024 ** 2:
        return f"{b / (1024 ** 2):.1f} MB"
    elif b >= 1024:
        return f"{b / 1024:.0f} KB"
    return f"{b} B"


@app.get("/api/account/storage")
def get_account_storage():
    """Returns real storage quota and user profile from Google Drive API."""
    service = auth.get_drive_service()
    about = service.about().get(fields="storageQuota,user").execute()
    user = about.get("user", {})
    quota = about.get("storageQuota", {})

    limit = int(quota.get("limit", 0))
    usage = int(quota.get("usage", 0))
    usage_drive = int(quota.get("usageInDrive", 0))
    usage_trash = int(quota.get("usageInDriveTrash", 0))
    usage_other = max(0, usage - usage_drive)

    free_bytes = max(0, limit - usage) if limit > 0 else 0

    return {
        "user": {
            "name": user.get("displayName", "User"),
            "email": user.get("emailAddress", ""),
            "avatar": user.get("photoLink", ""),
        },
        "quota": {
            "limit_bytes": limit,
            "usage_bytes": usage,
            "drive_bytes": usage_drive,
            "other_bytes": usage_other,
            "trash_bytes": usage_trash,
            "free_bytes": free_bytes,
            "limit_formatted": _format_bytes(limit),
            "usage_formatted": _format_bytes(usage),
            "drive_formatted": _format_bytes(usage_drive),
            "other_formatted": _format_bytes(usage_other),
            "free_formatted": _format_bytes(free_bytes),
            "drive_percent": round((usage_drive / limit * 100), 2) if limit > 0 else 0,
            "other_percent": round((usage_other / limit * 100), 2) if limit > 0 else 0,
            "free_percent": round((free_bytes / limit * 100), 2) if limit > 0 else 0,
            "total_used_percent": round((usage / limit * 100), 2) if limit > 0 else 0,
        }
    }


@app.get("/api/status")
def get_status():
    """Returns connection and account authorization status."""
    is_auth = auth.is_authenticated
    return {
        "authenticated": is_auth,
        "account": "tejaguru027@gmail.com" if is_auth else None,
        "has_credentials": auth.has_credentials
    }


@app.get("/api/drive/scan")
def scan_drive(folder_id: str = "root", recursive: bool = False):
    """Scans Google Drive and returns categorized files and duplicates."""
    service = auth.get_drive_service()
    scanner = DriveScanner(service)
    items = scanner.fetch_items(folder_id=folder_id, recursive=recursive)

    dup_map = scanner.identify_duplicates(items)
    organizer = DriveOrganizer(service)
    plan = organizer.build_plan(items, duplicate_map=dup_map)

    results = []
    for p in plan:
        results.append({
            "id": p.item.id,
            "name": p.item.name,
            "mime_type": p.item.mime_type,
            "size": p.item.size,
            "category": p.target_category,
            "reason": p.reason,
            "is_duplicate": p.is_duplicate,
            "master_name": p.master_name,
            "thumbnail_link": p.item.thumbnail_link,
            "web_view_link": p.item.web_view_link,
            "icon_link": p.item.icon_link,
            "master_id": p.master_id,
            "master_thumbnail": p.master_thumbnail,
            "master_web_view": p.master_web_view,
        })

    return {
        "total_files": len(items),
        "categorized_count": len(results),
        "duplicate_count": len(dup_map),
        "files": results
    }


@app.post("/api/drive/organize")
def organize_drive(req: MoveRequest):
    """Executes or previews Google Drive file moves."""
    service = auth.get_drive_service()
    scanner = DriveScanner(service)
    items = scanner.fetch_items(folder_id=req.folder_id)

    dup_map = scanner.identify_duplicates(items)
    organizer = DriveOrganizer(service)
    plan = organizer.build_plan(items, duplicate_map=dup_map)

    # Filter by specific file IDs if provided
    if req.file_ids:
        plan = [p for p in plan if p.item.id in req.file_ids]

    if req.dry_run:
        return {
            "dry_run": True,
            "planned_moves": len(plan),
            "message": f"Simulation mode: {len(plan)} files would be moved into organized cloud folders."
        }

    result = organizer.execute_plan(plan, root_id=req.folder_id)
    return {
        "dry_run": False,
        "session_id": result["session_id"],
        "moved_count": result["moved_count"],
        "errors": result["errors"]
    }


@app.post("/api/drive/undo")
def rollback_session(req: UndoRequest):
    """Rolls back the last or specified organization session."""
    service = auth.get_drive_service()
    organizer = DriveOrganizer(service)
    res = organizer.rollback_session(session_id=req.session_id)
    return res


@app.get("/api/history")
def get_history():
    """Returns transaction history list."""
    journal = CloudJournal()
    return journal.list_sessions()


@app.get("/api/photos/scan")
def scan_photos():
    """Scans Google Photos media items, albums, and burst shots."""
    try:
        service = auth.get_photos_service()
        scanner = PhotosScanner(service)
        photos = scanner.fetch_media_items(max_items=300)
        albums = scanner.cluster_by_album(photos)
        bursts = scanner.detect_burst_duplicates(photos)

        album_summary = [
            {"album_name": name, "count": len(group), "sample": [p.filename for p in group[:3]]}
            for name, group in albums.items()
        ]
        burst_summary = [
            {"count": len(b), "timestamp": b[0].creation_time, "files": [p.filename for p in b]}
            for b in bursts
        ]

        return {
            "total_photos": len(photos),
            "albums": album_summary,
            "bursts": burst_summary
        }
    except Exception as e:
        return {
            "total_photos": 0,
            "albums": [],
            "bursts": [],
            "error": str(e)
        }


# Mount static files to serve the Google AI Studio UI directly at http://localhost:8000/
from pathlib import Path
from fastapi.staticfiles import StaticFiles

static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
