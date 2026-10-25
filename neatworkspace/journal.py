"""Transaction journal and audit history for NeatWorkspace Cloud Rollback / Undo."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import HISTORY_JOURNAL_PATH


class CloudJournal:
    """Manages transactional audit history for reversible Google Drive organization."""

    def __init__(self, db_path: Path = HISTORY_JOURNAL_PATH):
        self.db_path = db_path
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_data([])

    def _read_data(self) -> List[Dict[str, Any]]:
        if not self.db_path.exists():
            return []
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [s for s in data if isinstance(s, dict) and "session_id" in s]
                return []
        except (json.JSONDecodeError, OSError):
            return []

    def _write_data(self, data: List[Dict[str, Any]]) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def record_session(
        self,
        session_id: str,
        moves: List[Dict[str, Any]],
        created_folders: List[Dict[str, str]]
    ) -> None:
        """Record a completed Google Drive cloud move transaction."""
        sessions = self._read_data()
        session_record = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "move_count": len(moves),
            "moves": moves,
            "created_folders": created_folders,
            "status": "completed"
        }
        sessions.append(session_record)
        self._write_data(sessions)

    def get_last_session(self) -> Optional[Dict[str, Any]]:
        """Return the most recent active cloud session that has not yet been undone."""
        sessions = self._read_data()
        for s in reversed(sessions):
            if s.get("status") == "completed":
                return s
        return None

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Look up a session by its unique ID."""
        for s in self._read_data():
            if s.get("session_id") == session_id:
                return s
        return None

    def mark_session_undone(self, session_id: str) -> None:
        """Mark a cloud session as undone."""
        sessions = self._read_data()
        for s in sessions:
            if s.get("session_id") == session_id:
                s["status"] = "undone"
                s["undone_at"] = datetime.now().isoformat()
        self._write_data(sessions)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all recorded cloud sessions."""
        return self._read_data()
