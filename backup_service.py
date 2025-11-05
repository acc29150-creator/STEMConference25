"""
═══════════════════════════════════════════════════════════════════════════════
CSV BACKUP SERVICE - Automatic local backups of all Firebase data
Dr. Crenshaw • Chattanooga State Community College

This module automatically backs up all student data to CSV files for:
- Data safety (local redundancy)
- Easy analysis in Excel/Sheets
- Long-term archival
═══════════════════════════════════════════════════════════════════════════════
"""
import csv
import os
import pytz
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any


class BackupService:
    """Handles automatic CSV backups of all tutoring data."""

    def __init__(self, backup_dir: str = "backups"):
        """
        Initialize the backup service.

        Args:
            backup_dir: Directory to store CSV backups (default: ./backups)
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        print(f"[BACKUP] CSV backup directory: {self.backup_dir.absolute()}")

    def _get_timestamp(self) -> str:
        """Get current timestamp for filenames."""
        return datetime.now(pytz.utc).strftime("%Y%m%d_%H%M%S")

    def _get_date_prefix(self) -> str:
        """Get date prefix for daily files."""
        return datetime.now(pytz.utc).strftime("%Y-%m-%d")

    def backup_users(self, users: Dict[str, Any]) -> str:
        """
        Backup user data to CSV.

        Args:
            users: Dictionary of user data

        Returns:
            Path to the created CSV file
        """
        filename = f"{self._get_date_prefix()}_users.csv"
        filepath = self.backup_dir / filename

        if not users:
            print("[BACKUP] No users to backup")
            return str(filepath)

        # Define CSV headers
        headers = [
            "user_token",
            "name",
            "created",
            "last_seen",
            "total_interactions",
            "total_sessions",
            "session_ids"
        ]

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()

                for user_token, user_data in users.items():
                    row = {
                        "user_token": user_token,
                        "name": user_data.get("name", ""),
                        "created": user_data.get("created", ""),
                        "last_seen": user_data.get("last_seen", ""),
                        "total_interactions": user_data.get("total_interactions", 0),
                        "total_sessions": len(user_data.get("sessions", [])),
                        "session_ids": "; ".join(user_data.get("sessions", []))
                    }
                    writer.writerow(row)

            print(f"[BACKUP] Saved {len(users)} users to {filename}")
            return str(filepath)

        except Exception as e:
            print(f"[BACKUP ERROR] Failed to backup users: {e}")
            return str(filepath)

    def backup_sessions(self, sessions: Dict[str, Any]) -> str:
        """
        Backup session data to CSV.

        Args:
            sessions: Dictionary of session data

        Returns:
            Path to the created CSV file
        """
        filename = f"{self._get_date_prefix()}_sessions.csv"
        filepath = self.backup_dir / filename

        if not sessions:
            print("[BACKUP] No sessions to backup")
            return str(filepath)

        # Define CSV headers
        headers = [
            "session_id",
            "user_token",
            "user_name",
            "module",
            "mode",
            "started",
            "last_activity",
            "ended",
            "duration_minutes",
            "original_problem",
            "problem_completed",
            "steps_completed",
            "hints_requested",
            "why_requested",
            "problems_solved",
            "comprehension_checks",
            "total_messages"
        ]

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()

                for session_id, session_data in sessions.items():
                    # Calculate duration in minutes
                    duration_min = 0
                    if session_data.get("duration_seconds"):
                        duration_min = round(session_data["duration_seconds"] / 60, 1)

                    row = {
                        "session_id": session_id,
                        "user_token": session_data.get("user_token", ""),
                        "user_name": "",  # Will be looked up if needed
                        "module": session_data.get("module", ""),
                        "mode": session_data.get("mode", ""),
                        "started": session_data.get("started", ""),
                        "last_activity": session_data.get("last_activity", ""),
                        "ended": session_data.get("ended", ""),
                        "duration_minutes": duration_min,
                        "original_problem": (session_data.get("original_problem", "") or "")[:200],  # Truncate
                        "problem_completed": session_data.get("problem_completed", False),
                        "steps_completed": session_data.get("steps_completed", 0),
                        "hints_requested": session_data.get("hints_requested", 0),
                        "why_requested": session_data.get("why_requested", 0),
                        "problems_solved": session_data.get("problems_solved", 0),
                        "comprehension_checks": "; ".join(session_data.get("comprehension_checks", [])),
                        "total_messages": len(session_data.get("messages", []))
                    }
                    writer.writerow(row)

            print(f"[BACKUP] Saved {len(sessions)} sessions to {filename}")
            return str(filepath)

        except Exception as e:
            print(f"[BACKUP ERROR] Failed to backup sessions: {e}")
            return str(filepath)

    def backup_chat_messages(self, sessions: Dict[str, Any]) -> str:
        """
        Backup all chat messages to CSV.

        Args:
            sessions: Dictionary of session data containing messages

        Returns:
            Path to the created CSV file
        """
        filename = f"{self._get_date_prefix()}_chat_messages.csv"
        filepath = self.backup_dir / filename

        # Define CSV headers
        headers = [
            "session_id",
            "message_number",
            "timestamp",
            "role",
            "content",
            "has_image"
        ]

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()

                total_messages = 0
                for session_id, session_data in sessions.items():
                    messages = session_data.get("messages", [])

                    for idx, message in enumerate(messages, 1):
                        # Extract content from message
                        content = ""
                        has_image = False

                        if isinstance(message.get("content"), list):
                            # Multi-part content (text + images)
                            for part in message["content"]:
                                if part.get("type") == "text":
                                    content = part.get("text", "")
                                elif part.get("type") == "image_url":
                                    has_image = True
                        else:
                            # Simple text content
                            content = message.get("content", "")

                        row = {
                            "session_id": session_id,
                            "message_number": idx,
                            "timestamp": session_data.get("last_activity", ""),
                            "role": message.get("role", ""),
                            "content": content[:500],  # Truncate long messages
                            "has_image": has_image
                        }
                        writer.writerow(row)
                        total_messages += 1

            print(f"[BACKUP] Saved {total_messages} chat messages to {filename}")
            return str(filepath)

        except Exception as e:
            print(f"[BACKUP ERROR] Failed to backup chat messages: {e}")
            return str(filepath)

    def backup_reports(self, reports: List[Dict[str, Any]]) -> str:
        """
        Backup problem reports to CSV.

        Args:
            reports: List of problem reports

        Returns:
            Path to the created CSV file
        """
        filename = f"{self._get_date_prefix()}_reports.csv"
        filepath = self.backup_dir / filename

        if not reports:
            print("[BACKUP] No reports to backup")
            return str(filepath)

        # Define CSV headers
        headers = [
            "timestamp",
            "user_token",
            "session_id",
            "category",
            "report"
        ]

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()

                for report in reports:
                    row = {
                        "timestamp": report.get("timestamp", ""),
                        "user_token": report.get("user_token", ""),
                        "session_id": report.get("session_id", ""),
                        "category": report.get("category", ""),
                        "report": report.get("report", "")
                    }
                    writer.writerow(row)

            print(f"[BACKUP] Saved {len(reports)} reports to {filename}")
            return str(filepath)

        except Exception as e:
            print(f"[BACKUP ERROR] Failed to backup reports: {e}")
            return str(filepath)

    def _verify_backup_integrity(self, current_sessions: Dict) -> None:
        """
        Verify backup integrity by comparing with previous backup.
        Warns if session count drops significantly (possible data loss).

        Args:
            current_sessions: Current session data being backed up
        """
        try:
            # Find most recent previous backup file
            session_files = sorted(self.backup_dir.glob("*_sessions.csv"))

            if len(session_files) < 2:
                # Not enough backups to compare
                return

            # Get the second-most recent file (previous backup)
            previous_file = session_files[-2]

            # Count sessions in previous backup
            with open(previous_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                previous_count = sum(1 for _ in reader)

            current_count = len(current_sessions)

            # Check for significant data loss (>30% decrease)
            if current_count < previous_count * 0.7:
                loss_percent = int((1 - current_count / previous_count) * 100)
                print(f"\n{'='*80}")
                print(f"⚠️  BACKUP ANOMALY DETECTED")
                print(f"{'='*80}")
                print(f"Previous backup: {previous_count} sessions")
                print(f"Current backup:  {current_count} sessions")
                print(f"Data loss:       {loss_percent}% ({previous_count - current_count} sessions)")
                print(f"\nPOSSIBLE CAUSES:")
                print(f"  1. Migration script ran and overwrote Firebase with old data")
                print(f"  2. Sessions were archived or deleted")
                print(f"  3. Database was reset or restored from old backup")
                print(f"\nACTION REQUIRED:")
                print(f"  - Check /health/data endpoint for data integrity status")
                print(f"  - Review DATA_LOSS_ROOT_CAUSE_REPORT.md")
                print(f"  - Verify Firebase hasn't been overwritten")
                print(f"{'='*80}\n")

            # Check for unusually old data
            session_dates = [s.get('started', '')[:10] for s in current_sessions.values() if s.get('started')]
            if session_dates:
                latest_date = max(session_dates)
                try:
                    # Parse date safely
                    latest_dt = datetime.fromisoformat(latest_date + "T00:00:00")
                    if not latest_dt.tzinfo:
                        latest_dt = latest_dt.replace(tzinfo=pytz.utc)
                    days_old = (datetime.now(pytz.utc) - latest_dt).days

                    if days_old > 7 and current_count > 0:
                        print(f"\n{'='*80}")
                        print(f"⚠️  OLD DATA WARNING")
                        print(f"{'='*80}")
                        print(f"Latest session is {days_old} days old ({latest_date})")
                        print(f"This suggests database may contain only archived/old data")
                        print(f"Check /health/data endpoint for details")
                        print(f"{'='*80}\n")
                except (ValueError, TypeError):
                    pass  # Skip if date parsing fails

        except Exception as e:
            print(f"[BACKUP WARNING] Could not verify backup integrity: {e}")

    def backup_all(self, users: Dict, sessions: Dict, reports: List) -> Dict[str, str]:
        """
        Backup all data to CSV files with integrity verification.

        Args:
            users: User data dictionary
            sessions: Session data dictionary
            reports: Reports list

        Returns:
            Dictionary mapping backup type to file path
        """
        print(f"\n[BACKUP] Starting full backup at {datetime.now(pytz.utc).strftime('%I:%M %p UTC')}")

        # Verify backup integrity before creating new backup
        self._verify_backup_integrity(sessions)

        backup_files = {
            "users": self.backup_users(users),
            "sessions": self.backup_sessions(sessions),
            "messages": self.backup_chat_messages(sessions),
            "reports": self.backup_reports(reports)
        }

        print(f"[BACKUP] Full backup complete")
        print(f"[BACKUP] Files saved to: {self.backup_dir.absolute()}\n")

        return backup_files

    def cleanup_old_backups(self, days_to_keep: int = 365):
        """
        Delete backup files older than specified days.

        Args:
            days_to_keep: Number of days to keep backups (default: 365 = 12 months)
        """
        try:
            cutoff_date = datetime.now(pytz.utc) - timedelta(days=days_to_keep)

            deleted_count = 0
            for filepath in self.backup_dir.glob("*.csv"):
                # Get file modification time
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime, tz=pytz.utc)

                if mtime < cutoff_date:
                    filepath.unlink()
                    deleted_count += 1

            if deleted_count > 0:
                print(f"[BACKUP] Deleted {deleted_count} old backup files (>{days_to_keep} days)")

        except Exception as e:
            print(f"[BACKUP ERROR] Failed to cleanup old backups: {e}")


# ═══════════════════════════════════════════════════════════════════════════
#                    AUTOMATIC BACKUP SCHEDULER
# ═══════════════════════════════════════════════════════════════════════════

class AutoBackupScheduler:
    """Automatically backs up data at regular intervals."""

    def __init__(self, backup_service: BackupService, interval_hours: int = 6):
        """
        Initialize the auto-backup scheduler.

        Args:
            backup_service: BackupService instance
            interval_hours: Hours between backups (default: 6)
        """
        self.backup_service = backup_service
        self.interval_seconds = interval_hours * 3600
        self.stop_event = threading.Event()
        self.thread = None

    def _backup_worker(self, get_data_callback):
        """Background worker that performs backups on schedule."""
        while not self.stop_event.is_set():
            try:
                # Get current data from callback
                users, sessions, reports = get_data_callback()

                # Perform backup
                self.backup_service.backup_all(users, sessions, reports)

                # Cleanup old backups (keep 12 months)
                self.backup_service.cleanup_old_backups(days_to_keep=365)

            except Exception as e:
                print(f"[BACKUP ERROR] Auto-backup failed: {e}")

            # Wait for next backup or stop signal
            self.stop_event.wait(self.interval_seconds)

    def start(self, get_data_callback):
        """
        Start the automatic backup scheduler.

        Args:
            get_data_callback: Function that returns (users, sessions, reports)
        """
        if self.thread and self.thread.is_alive():
            print("[BACKUP] Auto-backup already running")
            return

        print(f"[BACKUP] Starting auto-backup every {self.interval_seconds // 3600} hours")
        self.thread = threading.Thread(
            target=self._backup_worker,
            args=(get_data_callback,),
            daemon=True
        )
        self.thread.start()

    def stop(self):
        """Stop the automatic backup scheduler."""
        print("[BACKUP] Stopping auto-backup scheduler")
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
