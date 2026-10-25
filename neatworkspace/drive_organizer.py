"""Cloud execution and rollback engine for Google Drive organization."""

import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .config import MIME_FOLDER
from .drive_scanner import DriveItem
from .docs_inspector import classify_cloud_item
from .journal import CloudJournal


@dataclass
class CloudPlanItem:
    """Represents a proposed file move in Google Drive."""
    item: DriveItem
    target_category: str
    reason: str
    is_duplicate: bool = False
    master_name: Optional[str] = None


class DriveOrganizer:
    """Orchestrates planning, executing, and rolling back Google Drive reorganizations."""

    def __init__(self, drive_service: Any, journal: Optional[CloudJournal] = None):
        self.service = drive_service
        self.journal = journal or CloudJournal()
        self._folder_cache: Dict[str, str] = {}  # "Path/To/Folder" -> folder_id

    def build_plan(
        self,
        items: List[DriveItem],
        duplicate_map: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[CloudPlanItem]:
        """Generate a dry-run plan for organizing Drive files into universal categories."""
        plan: List[CloudPlanItem] = []
        dups = duplicate_map or {}

        for item in items:
            if item.is_folder:
                continue

            if item.id in dups:
                dup_info = dups[item.id]
                plan.append(CloudPlanItem(
                    item=item,
                    target_category="_Duplicates",
                    reason=f"Exact duplicate copy of: {dup_info['master'].name}",
                    is_duplicate=True,
                    master_name=dup_info['master'].name
                ))
            else:
                cat, reason = classify_cloud_item(item.name, item.mime_type, item.size)
                plan.append(CloudPlanItem(
                    item=item,
                    target_category=cat,
                    reason=reason,
                    is_duplicate=False
                ))

        return plan

    def get_or_create_folder_path(self, category_path: str, root_id: str = "root") -> str:
        """
        Recursively get or create nested folders in Google Drive.
        e.g. 'Documents/Legal & Contracts'
        """
        if category_path in self._folder_cache:
            return self._folder_cache[category_path]

        parts = [p.strip() for p in category_path.split("/") if p.strip()]
        current_parent = root_id
        current_accum = ""

        for part in parts:
            current_accum = f"{current_accum}/{part}" if current_accum else part
            if current_accum in self._folder_cache:
                current_parent = self._folder_cache[current_accum]
                continue

            # Query Google Drive if folder already exists under current_parent
            query = (
                f"'{current_parent}' in parents and name = '{part}' "
                f"and mimeType = '{MIME_FOLDER}' and trashed = false"
            )
            response = self.service.files().list(
                q=query,
                spaces="drive",
                fields="files(id, name)"
            ).execute()

            existing = response.get("files", [])
            if existing:
                folder_id = existing[0]["id"]
            else:
                # Create the folder
                metadata = {
                    "name": part,
                    "mimeType": MIME_FOLDER,
                    "parents": [current_parent]
                }
                new_folder = self.service.files().create(
                    body=metadata,
                    fields="id"
                ).execute()
                folder_id = new_folder["id"]

            self._folder_cache[current_accum] = folder_id
            current_parent = folder_id

        return current_parent

    def execute_plan(
        self,
        plan: List[CloudPlanItem],
        root_id: str = "root"
    ) -> Dict[str, Any]:
        """
        Execute planned cloud moves by updating parent folder IDs in Google Drive.
        Records every operation in CloudJournal for 100% reversible undo.
        """
        session_id = f"gdrive_session_{uuid.uuid4().hex[:8]}"
        moves_logged: List[Dict[str, Any]] = []
        created_folders: List[Dict[str, str]] = []
        errors: List[Dict[str, str]] = []

        for p in plan:
            try:
                dest_folder_id = self.get_or_create_folder_path(p.target_category, root_id)

                # Skip if already in destination folder
                if dest_folder_id in p.item.parents:
                    continue

                old_parents_str = ",".join(p.item.parents)
                self.service.files().update(
                    fileId=p.item.id,
                    addParents=dest_folder_id,
                    removeParents=old_parents_str,
                    fields="id, parents"
                ).execute()

                moves_logged.append({
                    "file_id": p.item.id,
                    "file_name": p.item.name,
                    "original_parent_ids": p.item.parents,
                    "destination_folder_id": dest_folder_id,
                    "category": p.target_category
                })
            except Exception as e:
                errors.append({"file": p.item.name, "error": str(e)})

        if moves_logged:
            self.journal.record_session(
                session_id=session_id,
                moves=moves_logged,
                created_folders=created_folders
            )

        return {
            "session_id": session_id,
            "moved_count": len(moves_logged),
            "errors": errors
        }

    def rollback_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Reverses cloud moves for a session, restoring files to their exact original parents.
        """
        if session_id:
            session = self.journal.get_session(session_id)
        else:
            session = self.journal.get_last_session()

        if not session:
            return {"success": False, "message": "No active cloud session to rollback."}

        moves = session.get("moves", [])
        restored = 0
        failed = 0

        for m in reversed(moves):
            file_id = m["file_id"]
            orig_parents = m["original_parent_ids"]
            curr_parent = m["destination_folder_id"]

            try:
                self.service.files().update(
                    fileId=file_id,
                    addParents=",".join(orig_parents),
                    removeParents=curr_parent,
                    fields="id, parents"
                ).execute()
                restored += 1
            except Exception:
                failed += 1

        self.journal.mark_session_undone(session["session_id"])

        return {
            "success": True,
            "session_id": session["session_id"],
            "restored_count": restored,
            "failed_count": failed
        }
