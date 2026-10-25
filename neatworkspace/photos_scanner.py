"""Scanner, date-clustering, and duplicate burst detector for Google Photos."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PhotoItem:
    """Represents a media item in Google Photos."""
    id: str
    filename: str
    mime_type: str
    creation_time: str
    width: Optional[int] = None
    height: Optional[int] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None

    @property
    def parsed_date(self) -> Optional[datetime]:
        try:
            # Format: "2026-10-25T11:22:33Z" or with timezone offset
            clean_time = self.creation_time.replace("Z", "+00:00")
            return datetime.fromisoformat(clean_time)
        except Exception:
            return None

    @property
    def target_album_name(self) -> str:
        dt = self.parsed_date
        if dt:
            month_name = dt.strftime("%B")
            return f"NeatPhotos {dt.year} {dt.strftime('%m')}-{month_name}"
        return "NeatPhotos Unsorted"

    @property
    def is_screenshot(self) -> bool:
        lower = self.filename.lower()
        return "screenshot" in lower or "screen_shot" in lower or "capture" in lower


class PhotosScanner:
    """Scans Google Photos media items, clusters into albums, and detects burst clutter."""

    def __init__(self, photos_service: Any):
        self.service = photos_service

    def fetch_media_items(self, page_size: int = 100, max_items: int = 500) -> List[PhotoItem]:
        """Fetch media items from Google Photos Library API."""
        items: List[PhotoItem] = []
        page_token = None

        while len(items) < max_items:
            req_body: Dict[str, Any] = {"pageSize": page_size}
            if page_token:
                req_body["pageToken"] = page_token

            response = self.service.mediaItems().list(**req_body).execute()
            media = response.get("mediaItems", [])

            for m in media:
                meta = m.get("mediaMetadata", {})
                photo_meta = meta.get("photo", {})
                items.append(PhotoItem(
                    id=m["id"],
                    filename=m.get("filename", "Photo"),
                    mime_type=m.get("mimeType", "image/jpeg"),
                    creation_time=meta.get("creationTime", datetime.now().isoformat()),
                    width=int(meta["width"]) if "width" in meta else None,
                    height=int(meta["height"]) if "height" in meta else None,
                    camera_make=photo_meta.get("cameraMake"),
                    camera_model=photo_meta.get("cameraModel")
                ))

            page_token = response.get("nextPageToken")
            if not page_token or not media:
                break

        return items

    def cluster_by_album(self, items: List[PhotoItem]) -> Dict[str, List[PhotoItem]]:
        """Cluster photos into chronological Year/Month albums."""
        clusters: Dict[str, List[PhotoItem]] = {}
        for photo in items:
            album = photo.target_album_name
            clusters.setdefault(album, []).append(photo)
        return clusters

    def detect_burst_duplicates(self, items: List[PhotoItem], threshold_seconds: int = 3) -> List[List[PhotoItem]]:
        """
        Detects rapid camera burst shots (photos taken within threshold_seconds with identical resolution).
        """
        dated_items = [it for it in items if it.parsed_date is not None]
        dated_items.sort(key=lambda x: x.parsed_date)  # type: ignore

        burst_groups: List[List[PhotoItem]] = []
        current_group: List[PhotoItem] = []

        for item in dated_items:
            if not current_group:
                current_group.append(item)
                continue

            last = current_group[-1]
            diff = abs((item.parsed_date - last.parsed_date).total_seconds())  # type: ignore
            same_res = (item.width == last.width and item.height == last.height)

            if diff <= threshold_seconds and same_res:
                current_group.append(item)
            else:
                if len(current_group) > 1:
                    burst_groups.append(current_group)
                current_group = [item]

        if len(current_group) > 1:
            burst_groups.append(current_group)

        return burst_groups
