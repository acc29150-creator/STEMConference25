"""
Email Service for Math 1710 AI Tutor
Handles immediate alerts and weekly digest emails for problem reports.

Author: Dr. April Crenshaw
Institution: Chattanooga State Community College
"""

import smtplib
import pytz
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path
import json


class EmailService:
    """
    Manages email notifications for student problem reports.

    Features:
    - Immediate emails for critical issues (math errors, accessibility)
    - Weekly digest emails (sent every Friday) for non-critical issues
    - HTML-formatted emails with session context
    """

    # Categories that trigger immediate emails
    CRITICAL_CATEGORIES = {"math_error", "accessibility"}

    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        from_email: str = "",
        to_email: str = "april.crenshaw@chattanoogastate.edu",
        reports_file: str = "data/pending_reports.json"
    ):
        """
        Initialize email service.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port (587 for TLS)
            smtp_user: SMTP username
            smtp_password: SMTP password or app-specific password
            from_email: From address for sent emails
            to_email: Recipient email address
            reports_file: Path to store pending reports for weekly digest
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email or smtp_user
        self.to_email = to_email
        self.reports_file = Path(reports_file)

        # Ensure reports directory exists
        self.reports_file.parent.mkdir(parents=True, exist_ok=True)

    def send_email(self, subject: str, html_body: str) -> bool:
        """
        Send an email via SMTP.

        Args:
            subject: Email subject line
            html_body: HTML content of email

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = self.to_email

            # Attach HTML body
            html_part = MIMEText(html_body, "html")
            msg.attach(html_part)

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print(f"[EMAIL] Sent: {subject}")
            return True

        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send email: {e}")
            return False

    def send_immediate_alert(self, report: Dict[str, Any]) -> bool:
        """
        Send immediate email for critical issues.

        Args:
            report: Report dictionary with keys:
                - category: Issue category
                - report: Issue description
                - user_name: Student name
                - session_id: Session identifier
                - timestamp: ISO timestamp
                - module: Course unit

        Returns:
            True if sent successfully
        """
        category_labels = {
            "math_error": "🚨 MATH ERROR",
            "accessibility": "♿ ACCESSIBILITY ISSUE"
        }

        category_label = category_labels.get(
            report["category"],
            report["category"].replace("_", " ").title()
        )

        subject = f"{category_label} - MATH 1710 Tutor Report"

        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(report["timestamp"].replace("Z", "+00:00"))
            time_str = timestamp.strftime("%b %d, %Y at %I:%M %p")
        except:
            time_str = report.get("timestamp", "Unknown time")

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #2563eb, #1e40af); color: white;
                   padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb;
                    border-top: none; border-radius: 0 0 8px 8px; }}
        .field {{ margin-bottom: 15px; }}
        .label {{ font-weight: bold; color: #1e40af; }}
        .alert {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 15px;
                  margin-top: 15px; border-radius: 4px; }}
        .footer {{ margin-top: 20px; font-size: 14px; color: #6b7280; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">{category_label}</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">Immediate Attention Required</p>
        </div>
        <div class="content">
            <div class="field">
                <span class="label">Student:</span> {report.get('user_name', 'Unknown')}
            </div>
            <div class="field">
                <span class="label">Unit:</span> {report.get('module', 'Unknown')}
            </div>
            <div class="field">
                <span class="label">Time:</span> {time_str}
            </div>
            <div class="alert">
                <p style="margin: 0 0 10px 0;"><strong>Issue Description:</strong></p>
                <p style="margin: 0;">{report.get('report', 'No description provided')}</p>
            </div>
            <div class="field" style="margin-top: 15px;">
                <span class="label">Session ID:</span> <code>{report.get('session_id', 'N/A')}</code>
            </div>
        </div>
        <div class="footer">
            <p>This is an automated alert from the MATH 1710 AI Tutoring System.</p>
            <p>Chattanooga State Community College</p>
        </div>
    </div>
</body>
</html>
"""

        return self.send_email(subject, html_body)

    def queue_report_for_digest(self, report: Dict[str, Any]) -> bool:
        """
        Add a non-critical report to the queue for weekly digest.

        Args:
            report: Report dictionary

        Returns:
            True if queued successfully
        """
        try:
            # Load existing reports
            if self.reports_file.exists():
                with open(self.reports_file, 'r') as f:
                    reports = json.load(f)
            else:
                reports = []

            # Add new report
            reports.append({
                **report,
                "queued_at": datetime.now(pytz.utc).isoformat()
            })

            # Save back to file
            with open(self.reports_file, 'w') as f:
                json.dump(reports, f, indent=2)

            print(f"[EMAIL] Queued report for weekly digest: {report['category']}")
            return True

        except Exception as e:
            print(f"[EMAIL ERROR] Failed to queue report: {e}")
            return False

    def send_weekly_digest(self) -> bool:
        """
        Send weekly digest email with all queued reports.
        Should be called every Friday.

        Returns:
            True if sent successfully
        """
        # Load pending reports
        if not self.reports_file.exists():
            print("[EMAIL] No pending reports for digest")
            return False

        try:
            with open(self.reports_file, 'r') as f:
                reports = json.load(f)
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to load reports: {e}")
            return False

        if not reports:
            print("[EMAIL] No pending reports for digest")
            return False

        # Group reports by category
        by_category = {}
        for report in reports:
            category = report.get("category", "other")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(report)

        # Generate date range for subject
        now = datetime.now(pytz.utc)
        week_ago = now - timedelta(days=7)
        date_range = f"{week_ago.strftime('%b %d')} - {now.strftime('%b %d, %Y')}"

        subject = f"📊 MATH 1710 Tutor - Weekly Report ({date_range})"

        # Build HTML sections for each category
        category_sections = []
        category_labels = {
            "unclear_explanation": "📝 Unclear Explanations",
            "ui_bug": "🐛 UI/Button Issues",
            "other": "📋 Other Feedback"
        }

        for category, category_reports in by_category.items():
            label = category_labels.get(category, category.replace("_", " ").title())

            items_html = ""
            for i, report in enumerate(category_reports, 1):
                try:
                    timestamp = datetime.fromisoformat(report["timestamp"].replace("Z", "+00:00"))
                    time_str = timestamp.strftime("%b %d, %I:%M %p")
                except:
                    time_str = "Unknown time"

                items_html += f"""
                <div class="report-item">
                    <div class="report-meta">
                        <strong>{i}. {time_str}</strong> - {report.get('user_name', 'Unknown')}
                    </div>
                    <div class="report-text">"{report.get('report', 'No description')}"</div>
                    <div class="report-session">Session: <code>{report.get('session_id', 'N/A')}</code></div>
                </div>
                """

            category_sections.append(f"""
            <div class="category-section">
                <h3>{label} ({len(category_reports)} report{'s' if len(category_reports) != 1 else ''})</h3>
                {items_html}
            </div>
            """)

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #2563eb, #1e40af); color: white;
                   padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: white; padding: 20px; border: 1px solid #e5e7eb;
                    border-top: none; }}
        .category-section {{ margin-bottom: 30px; padding: 15px;
                            background: #f9fafb; border-radius: 8px; }}
        .category-section h3 {{ margin-top: 0; color: #1e40af;
                                border-bottom: 2px solid #2563eb; padding-bottom: 8px; }}
        .report-item {{ padding: 12px; background: white; border-radius: 6px;
                        margin-bottom: 10px; border-left: 3px solid #2563eb; }}
        .report-meta {{ font-size: 14px; color: #6b7280; margin-bottom: 5px; }}
        .report-text {{ margin: 8px 0; }}
        .report-session {{ font-size: 13px; color: #9ca3af; }}
        code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 3px;
                font-family: monospace; font-size: 12px; }}
        .summary {{ background: #dbeafe; padding: 15px; border-radius: 8px;
                   margin-bottom: 20px; border-left: 4px solid #2563eb; }}
        .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb;
                  font-size: 14px; color: #6b7280; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">📊 MATH 1710 Weekly Report</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">{date_range}</p>
        </div>
        <div class="content">
            <div class="summary">
                <strong>Summary:</strong> You have {len(reports)} report{'s' if len(reports) != 1 else ''}
                to review from the past week.
            </div>

            {''.join(category_sections)}

            <div class="footer">
                <p><strong>Next Steps:</strong></p>
                <ul style="margin-top: 8px;">
                    <li>Review each report and session context</li>
                    <li>Update tutor prompts if patterns emerge</li>
                    <li>Respond to students if follow-up needed</li>
                </ul>
                <p style="margin-top: 15px;">
                    This digest is automatically sent every Friday.<br/>
                    Chattanooga State Community College - MATH 1710 AI Tutoring System
                </p>
            </div>
        </div>
    </div>
</body>
</html>
"""

        # Send the digest
        success = self.send_email(subject, html_body)

        # If successful, archive and clear the queue
        if success:
            archive_file = self.reports_file.parent / f"digest_archive_{now.strftime('%Y%m%d')}.json"
            with open(archive_file, 'w') as f:
                json.dump(reports, f, indent=2)

            # Clear the queue
            self.reports_file.unlink()
            print(f"[EMAIL] Sent weekly digest with {len(reports)} reports")

        return success

    def handle_report(self, report: Dict[str, Any]) -> bool:
        """
        Route a report to immediate email or weekly digest based on category.

        Args:
            report: Report dictionary

        Returns:
            True if handled successfully
        """
        category = report.get("category", "other")

        if category in self.CRITICAL_CATEGORIES:
            # Send immediate email
            return self.send_immediate_alert(report)
        else:
            # Queue for weekly digest
            return self.queue_report_for_digest(report)


# Scheduler function for weekly digest (call this from your main scheduler)
def should_send_weekly_digest() -> bool:
    """
    Check if today is Friday and we should send the weekly digest.

    Returns:
        True if today is Friday
    """
    now = datetime.now(pytz.utc)
    return now.weekday() == 4  # Friday is day 4 (Monday=0)


if __name__ == "__main__":
    # Test the email service
    print("Email Service Test")
    print("=" * 50)

    # Create test service (update with your credentials)
    service = EmailService(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_user="your-email@gmail.com",  # UPDATE THIS
        smtp_password="your-app-password",  # UPDATE THIS
        from_email="math1710-tutor@chattanoogastate.edu",
        to_email="april.crenshaw@chattanoogastate.edu"
    )

    # Test immediate alert
    print("\nTesting immediate alert...")
    test_report = {
        "category": "math_error",
        "report": "The tutor said that x² + 4 = 0 has real solutions, but it only has complex solutions.",
        "user_name": "Test Student",
        "session_id": "test_123",
        "timestamp": datetime.now(pytz.utc).isoformat(),
        "module": "Unit 2: Quadratics & Polynomials"
    }
    service.handle_report(test_report)

    # Test queuing for digest
    print("\nTesting digest queue...")
    test_report2 = {
        "category": "unclear_explanation",
        "report": "The explanation for completing the square was confusing.",
        "user_name": "Another Student",
        "session_id": "test_456",
        "timestamp": datetime.now(pytz.utc).isoformat(),
        "module": "Unit 2: Quadratics & Polynomials"
    }
    service.handle_report(test_report2)

    print("\n" + "=" * 50)
    print("Test complete! Check your email and data/pending_reports.json")
