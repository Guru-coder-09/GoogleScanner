"""Rich Terminal CLI interface for NeatWorkspace."""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import box

from .auth import AuthManager
from .drive_scanner import DriveScanner, DriveItem
from .drive_organizer import DriveOrganizer, CloudPlanItem
from .photos_scanner import PhotosScanner, PhotoItem
from .journal import CloudJournal

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(legacy_windows=False)


def print_banner():
    """Prints a styled banner for NeatWorkspace."""
    auth = AuthManager()
    status = "[bold green]Authenticated[/bold green]" if auth.is_authenticated else "[bold yellow]Setup Required (credentials.json)[/bold yellow]"

    banner_text = (
        "[bold cyan]✨ NeatWorkspace Workstation[/bold cyan] - [bold white]Intelligent Google Cloud Automation[/bold white]\n"
        f"[dim]Google Account Status:[/dim] {status}  •  [dim]Safety:[/dim] [green]Zero Deletions • Dry-Run Preview • 100% Rollback[/green]\n"
        "[dim]Google Drive • Google Docs/Sheets/Slides • Native MD5 Deduplication • Photos EXIF Albums[/dim]"
    )
    console.print(Panel(banner_text, style="blue", box=box.ROUNDED, expand=False))


def display_drive_plan_table(plan: List[CloudPlanItem]):
    """Displays a formatted table of proposed cloud moves."""
    if not plan:
        console.print("\n[green]✨ Google Drive folder is already clean and organized![/green]\n")
        return

    table = Table(
        title="📋 Proposed Google Drive Cloud Organization Plan",
        box=box.ROUNDED,
        header_style="bold magenta",
        show_lines=True
    )

    table.add_column("Type", justify="center", width=5)
    table.add_column("Cloud File Name", style="bold white", max_width=36, overflow="ellipsis")
    table.add_column("Target Cloud Folder", style="bold cyan", max_width=36)
    table.add_column("Classification Reason", style="dim", max_width=32)
    table.add_column("Status", justify="center", width=12)

    for item in plan:
        if item.is_duplicate:
            icon = "⚠️"
            badge = "[yellow]Duplicate[/yellow]"
        elif "google-apps.document" in item.item.mime_type:
            icon = "📄"
            badge = "[blue]Doc[/blue]"
        elif "google-apps.spreadsheet" in item.item.mime_type:
            icon = "📊"
            badge = "[green]Sheet[/green]"
        elif "google-apps.presentation" in item.item.mime_type:
            icon = "📽️"
            badge = "[yellow]Slide[/yellow]"
        elif item.item.name.endswith(".pdf"):
            icon = "📕"
            badge = "[red]PDF[/red]"
        else:
            icon = "📁"
            badge = "[white]File[/white]"

        table.add_row(
            icon,
            item.item.name,
            item.target_category,
            item.reason,
            badge
        )

    console.print(table)


def run_drive_workflow(
    auth: AuthManager,
    dry_run: bool = False,
    auto_approve: bool = False,
    folder_id: str = "root"
):
    """Executes the Google Drive scanning and organization workflow."""
    print_banner()
    if not auth.has_credentials and not auth.is_authenticated:
        console.print(Panel(
            "[bold red]Google OAuth Credentials Missing![/bold red]\n\n"
            "To connect your Google Drive & Photos, please download your [bold white]credentials.json[/bold white] "
            "from Google Cloud Console and place it at:\n"
            f"  -> [bold cyan]{auth.credentials_path.resolve()}[/bold cyan]\n\n"
            "Instructions are provided in the project README.",
            box=box.ROUNDED,
            style="red"
        ))
        return

    try:
        service = auth.get_drive_service()
    except Exception as e:
        console.print(f"[bold red]Authentication error:[/bold red] {e}\n")
        return

    console.print(f"\n[bold green]🔍 Scanning Google Drive folder: [cyan]{folder_id}[/cyan] ...[/bold green]")
    scanner = DriveScanner(service)
    items = scanner.fetch_items(folder_id=folder_id, recursive=False)

    if not items:
        console.print("[yellow]No files found to organize in this folder.[/yellow]\n")
        return

    console.print(f"Found [bold white]{len(items)}[/bold white] files to evaluate.")

    # 1. Deduplication pass
    with console.status("[bold yellow]Scanning for duplicate files via native MD5 checksums...[/bold yellow]"):
        dup_map = scanner.identify_duplicates(items)

    # 2. Build Plan
    organizer = DriveOrganizer(service)
    plan = organizer.build_plan(items, duplicate_map=dup_map)

    dup_count = sum(1 for p in plan if p.is_duplicate)
    console.print(
        f"\n[bold white]Drive Analysis Summary:[/bold white] "
        f"[cyan]{len(plan)}[/cyan] files evaluated • "
        f"[yellow]{dup_count}[/yellow] exact duplicates detected (routed to _Duplicates/)\n"
    )

    display_drive_plan_table(plan)

    if dry_run:
        console.print("[bold yellow]🔍 Simulation mode (--sim): No cloud files were moved.[/bold yellow]\n")
        return

    confirm = auto_approve or Confirm.ask(f"[bold green]Apply changes to {len(plan)} Google Drive files?[/bold green]", default=True)
    if not confirm:
        console.print("[yellow]Operation canceled.[/yellow]\n")
        return

    with console.status("[bold green]Moving files into organized folders...[/bold green]"):
        res = organizer.execute_plan(plan, root_id=folder_id)

    console.print(f"\n[bold green]🎉 Successfully organized {res['moved_count']} files in Google Drive![/bold green]")
    console.print(f"[dim]Transaction Session ID: {res['session_id']}[/dim]")
    if res["errors"]:
        console.print(f"[bold red]⚠️ Errors ({len(res['errors'])}):[/bold red]")
        for err in res["errors"]:
            console.print(f"  • {err['file']}: {err['error']}")
    console.print("\n[bold cyan]Tip:[/bold cyan] To revert anytime, run: [bold white]python main.py --undo[/bold white]\n")


def run_photos_workflow(auth: AuthManager, dry_run: bool = False):
    """Executes Google Photos scanning, album clustering, and burst detection."""
    print_banner()
    if not auth.has_credentials and not auth.is_authenticated:
        console.print("[bold red]Please set up credentials.json first.[/bold red]\n")
        return

    try:
        service = auth.get_photos_service()
    except Exception as e:
        console.print(f"[bold red]Photos Authentication error:[/bold red] {e}\n")
        return

    console.print("\n[bold green]📸 Scanning Google Photos media items...[/bold green]")
    scanner = PhotosScanner(service)
    photos = scanner.fetch_media_items(max_items=300)

    if not photos:
        console.print("[yellow]No photos found in your Google Photos library.[/yellow]\n")
        return

    console.print(f"Found [bold white]{len(photos)}[/bold white] media items.")

    albums = scanner.cluster_by_album(photos)
    bursts = scanner.detect_burst_duplicates(photos)

    table = Table(title="📷 Proposed Google Photos Year/Month Album Organization", box=box.ROUNDED)
    table.add_column("Proposed Album Name", style="bold cyan")
    table.add_column("Photo Count", justify="center")
    table.add_column("Sample Media", style="dim", max_width=40)

    for album_name, group in sorted(albums.items()):
        samples = ", ".join(p.filename for p in group[:3])
        if len(group) > 3:
            samples += f", ... (+{len(group)-3} more)"
        table.add_row(album_name, str(len(group)), samples)

    console.print(table)

    if bursts:
        console.print(f"\n[bold yellow]⚠️ Detected {len(bursts)} rapid burst sequences (potential redundant photos):[/bold yellow]")
        for idx, b in enumerate(bursts[:5], 1):
            names = ", ".join(p.filename for p in b)
            console.print(f"  {idx}. [dim]{b[0].creation_time[:19]}[/dim]: {names} ({len(b)} photos)")

    if dry_run:
        console.print("\n[bold yellow]🔍 Simulation mode (--sim): No albums were created.[/bold yellow]\n")


def run_undo_workflow(auth: AuthManager, auto_approve: bool = False):
    """Rollback cloud moves using local journal."""
    journal = CloudJournal()
    last_session = journal.get_last_session()

    if not last_session:
        console.print("\n[yellow]⚠️ No active Google Drive session found to undo.[/yellow]\n")
        return

    console.print(Panel(
        f"[bold]Session ID:[/bold] {last_session['session_id']}\n"
        f"[bold]Date:[/bold] {last_session['timestamp']}\n"
        f"[bold]Cloud Files Moved:[/bold] {last_session['move_count']}",
        title="⏪ Cloud Session to Rollback",
        box=box.ROUNDED
    ))

    confirm = auto_approve or Confirm.ask("[bold red]Restore all files to their original Google Drive folders?[/bold red]", default=True)
    if not confirm:
        console.print("[yellow]Undo canceled.[/yellow]\n")
        return

    try:
        service = auth.get_drive_service()
    except Exception as e:
        console.print(f"[bold red]Drive service error:[/bold red] {e}\n")
        return

    organizer = DriveOrganizer(service, journal=journal)
    with console.status("[bold yellow]Restoring Google Drive files to original parent folders...[/bold yellow]"):
        result = organizer.rollback_session()

    if result["success"]:
        console.print(f"\n[bold green]✅ Rollback successful![/bold green] Restored {result['restored_count']} files in Google Drive.")
        if result['failed_count'] > 0:
            console.print(f"[yellow]Failed to restore: {result['failed_count']} files.[/yellow]")
    else:
        console.print(f"[red]❌ Rollback failed: {result.get('message')}[/red]\n")
