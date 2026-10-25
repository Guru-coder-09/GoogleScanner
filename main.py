"""Main CLI entrypoint for NeatWorkspace (Google Drive & Photos Automation Workstation)."""

import sys
import argparse
from pathlib import Path

# Ensure UTF-8 stdout encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from neatworkspace.auth import AuthManager
from neatworkspace.cli import (
    run_drive_workflow,
    run_photos_workflow,
    run_undo_workflow,
    print_banner
)


def main():
    parser = argparse.ArgumentParser(
        description="NeatWorkspace: Intelligent Google Workspace & Cloud Photos Automation Suite.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--drive", action="store_true", help="Organize Google Drive files into universal categories")
    parser.add_argument("--photos", action="store_true", help="Cluster Google Photos into chronological albums and detect bursts")
    parser.add_argument("--duplicates", action="store_true", help="Scan and quarantine duplicate cloud files")
    parser.add_argument("--folder", type=str, default="root", help="Target Google Drive folder ID (default: 'root')")
    parser.add_argument("--sim", "--dry-run", dest="dry_run", action="store_true", help="Simulation mode: preview changes without moving any cloud files")
    parser.add_argument("--undo", action="store_true", help="Roll back the most recent Google Drive organization session")
    parser.add_argument("-y", "--yes", action="store_true", help="Automatically approve and apply changes")

    args = parser.parse_args()
    auth = AuthManager()

    # 1. Rollback
    if args.undo:
        run_undo_workflow(auth, auto_approve=args.yes)
        return

    # 2. Photos
    if args.photos:
        run_photos_workflow(auth, dry_run=args.dry_run)
        return

    # 3. Drive / Duplicates
    if args.drive or args.duplicates:
        run_drive_workflow(
            auth,
            dry_run=args.dry_run,
            auto_approve=args.yes,
            folder_id=args.folder
        )
        return

    # Default: Banner and help guidance
    print_banner()
    parser.print_help()


if __name__ == "__main__":
    main()
