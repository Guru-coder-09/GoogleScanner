"""Scanner and duplicate detector for Google Drive and Google Workspace documents."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .config import MIME_FOLDER, PROTECTED_FOLDER_NAMES
from .docs_inspector import is_generic_title, classify_cloud_item


@dataclass
class DriveItem:
    """Represents a file or folder inside Google Drive."""
    id: str
    name: str
    mime_type: str
    parents: List[str]
    size: Optional[int] = None
    md5_checksum: Optional[str] = None
    created_time: Optional[str] = None
    modified_time: Optional[str] = None

    @property
    def is_folder(self) -> bool:
        return self.mime_type == MIME_FOLDER

    @property
    def is_generic(self) -> bool:
        return is_generic_title(self.name)


class DriveScanner:
    """Scans and analyzes files, duplicate hashes, and untitled documents in Google Drive."""

    def __init__(self, drive_service: Any):
        self.service = drive_service

    def fetch_items(
        self,
        folder_id: str = "root",
        recursive: bool = False,
        page_size: int = 1000
    ) -> List[DriveItem]:
        """Fetch files from Google Drive."""
        items: List[DriveItem] = []
        if recursive:
            query = "trashed = false"
        else:
            query = f"'{folder_id}' in parents and trashed = false"

        page_token = None
        fields = "nextPageToken, files(id, name, mimeType, parents, size, md5Checksum, createdTime, modifiedTime)"

        while True:
            response = self.service.files().list(
                q=query,
                spaces="drive",
                fields=fields,
                pageSize=page_size,
                pageToken=page_token
            ).execute()

            files = response.get("files", [])
            for f in files:
                # Skip protected or system folders
                if f.get("name", "").lower() in PROTECTED_FOLDER_NAMES:
                    continue

                items.append(DriveItem(
                    id=f["id"],
                    name=f.get("name", "Untitled"),
                    mime_type=f.get("mimeType", ""),
                    parents=f.get("parents", []),
                    size=int(f["size"]) if "size" in f else None,
                    md5_checksum=f.get("md5Checksum"),
                    created_time=f.get("createdTime"),
                    modified_time=f.get("modifiedTime")
                ))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return items

    def identify_duplicates(self, items: List[DriveItem]) -> Dict[str, Dict[str, Any]]:
        """
        Detects exact duplicate cloud files using Google Drive's native MD5 checksums.
        Returns: { duplicate_item_id: {'duplicate': DriveItem, 'master': DriveItem, 'hash': md5} }
        """
        hash_groups: Dict[str, List[DriveItem]] = {}
        for item in items:
            if not item.is_folder and item.md5_checksum:
                hash_groups.setdefault(item.md5_checksum, []).append(item)

        duplicates: Dict[str, Dict[str, Any]] = {}
        for md5_hash, group in hash_groups.items():
            if len(group) > 1:
                # Rank candidates: prioritize clean original name (no ' (1)', no 'Copy of')
                def clean_score(item: DriveItem) -> tuple[int, int]:
                    penalty = 0
                    if " (1)" in item.name or " (2)" in item.name:
                        penalty += 10
                    if item.name.lower().startswith("copy of"):
                        penalty += 10
                    return (penalty, len(item.name))

                sorted_group = sorted(group, key=clean_score)
                master = sorted_group[0]
                for copy in sorted_group[1:]:
                    duplicates[copy.id] = {
                        "duplicate": copy,
                        "master": master,
                        "hash": md5_hash
                    }

        return duplicates

    def identify_untitled_docs(self, items: List[DriveItem]) -> List[DriveItem]:
        """Finds all loose files with generic default titles (e.g. 'Untitled document')."""
        return [it for it in items if not it.is_folder and it.is_generic]

    def identify_empty_folders(self, all_items: List[DriveItem]) -> List[DriveItem]:
        """Find folders that have zero children."""
        folders = [it for it in all_items if it.is_folder]
        parent_ids = {p for it in all_items for p in it.parents}
        return [f for f in folders if f.id not in parent_ids]
