"""Google OAuth 2.0 Authentication and Token Management for NeatWorkspace."""

import os
from pathlib import Path
from typing import Optional, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import (
    DEFAULT_CREDENTIALS_PATH,
    ALT_CREDENTIALS_PATH,
    TOKEN_STORAGE_PATH,
    OAUTH_SCOPES
)


class AuthManager:
    """Manages Google OAuth 2.0 authentication flow, token refreshing, and API service construction."""

    def __init__(
        self,
        credentials_path: Optional[Path] = None,
        token_path: Path = TOKEN_STORAGE_PATH,
        scopes: list[str] = OAUTH_SCOPES
    ):
        self.credentials_path = credentials_path or self._locate_credentials()
        self.token_path = token_path
        self.scopes = scopes
        self._creds: Optional[Credentials] = None

    def _locate_credentials(self) -> Path:
        """Find credentials.json in either current folder or ~/.neatworkspace/."""
        if DEFAULT_CREDENTIALS_PATH.exists():
            return DEFAULT_CREDENTIALS_PATH
        if ALT_CREDENTIALS_PATH.exists():
            return ALT_CREDENTIALS_PATH
        return DEFAULT_CREDENTIALS_PATH

    @property
    def has_credentials(self) -> bool:
        """Check if client credentials JSON exists on disk."""
        return self.credentials_path.exists()

    @property
    def is_authenticated(self) -> bool:
        """Check if a valid or refreshable token is present."""
        creds = self.get_credentials(interactive=False)
        return creds is not None and (creds.valid or creds.refresh_token is not None)

    def get_credentials(self, interactive: bool = True) -> Optional[Credentials]:
        """Load cached token or initiate local OAuth 2.0 browser authorization flow."""
        if self._creds and self._creds.valid:
            return self._creds

        creds = None
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_path), self.scopes)
            except Exception:
                creds = None

        # Refresh expired token if possible
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(self.token_path, "w", encoding="utf-8") as token_file:
                    token_file.write(creds.to_json())
            except Exception:
                creds = None

        # Run local browser flow if needed and interactive
        if not creds and interactive:
            if not self.has_credentials:
                raise FileNotFoundError(
                    f"OAuth credentials not found! Place your Google OAuth client JSON at:\n"
                    f"  -> '{self.credentials_path.resolve()}' or '{ALT_CREDENTIALS_PATH}'"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_path),
                self.scopes
            )
            print("\n" + "=" * 70)
            print("🔑 GOOGLE OAUTH 2.0 AUTHORIZATION REQUIRED")
            print("=" * 70)
            creds = flow.run_local_server(
                port=0,
                prompt="consent",
                authorization_prompt_message="👉 Visit this URL to authorize NeatWorkspace:\n{url}\n",
                success_message="✅ NeatWorkspace authorized successfully! You can close this window."
            )

            # Save credentials for next run
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())

        self._creds = creds
        return creds

    def get_drive_service(self, creds: Optional[Credentials] = None) -> Any:
        """Build Google Drive API v3 resource service."""
        active_creds = creds or self.get_credentials()
        return build("drive", "v3", credentials=active_creds)

    def get_photos_service(self, creds: Optional[Credentials] = None) -> Any:
        """Build Google Photos Library API v1 resource service."""
        active_creds = creds or self.get_credentials()
        return build("photoslibrary", "v1", credentials=active_creds, static_discovery=False)
