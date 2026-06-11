# -*- coding: utf-8 -*-
"""
Weekly Inflation Alert
======================

Compares current inflation data with previous week's snapshot,
detects material changes, and sends a summary email.

This is a research-style data alert, not a marketing newsletter.
No analysis. No predictions. Just the data.

Usage:
    python send_weekly_alert.py

Environment variables required:
    RESEND_API_KEY - API key for Resend email service
    ALERT_RECIPIENTS - Comma-separated email addresses

Output:
    - data/weekly_snapshots.json (updated with new snapshot)
    - Email sent to recipients (if configured)
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Optional: load from .env
try:
    from dotenv import load_dotenv
    load_dotenv('.env.local')
    load_dotenv('.env')
except ImportError:
    pass

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Paths
DATA_DIR = "docs/data"
SNAPSHOTS_FILE = os.path.join(DATA_DIR, "weekly_snapshots.json")
CURRENT_DATA_FILE = os.path.join(DATA_DIR, "historical_cpi.json")

# Dashboard URL
DASHBOARD_URL = "https://jing-ny.github.io/inflation-dashboard/"

# Email configuration
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
ALERT_RECIPIENTS = os.environ.get("ALERT_RECIPIENTS", "").split(",")
ALERT_RECIPIENTS = [r.strip() for r in ALERT_RECIPIENTS if r.strip()]
SENDER_EMAIL = "onboarding@resend.dev"  # Resend test address (no domain verification needed)

# -----------------------------------------------------------------------------
# Material Change Rules (easily adjustable)
# -----------------------------------------------------------------------------

class ChangeRules:
    """
    Rules for determining material changes.
    Adjust these thresholds as needed.
    """
    # Minimum change in percentage points to be considered material
    MATERIAL_CHANGE_THRESHOLD_PP = 0.3
    
    # Threshold for direction determination
    # > +0.05 = rising, < -0.05 = falling, else stable
    DIRECTION_THRESHOLD_PP = 0.05
    
    @classmethod
    def is_material_change(cls, current: float, previous: float, 
                           current_direction: str, previous_direction: str) -> bool:
        """
        Determine if a change is material.
        
        Material if:
        1. Absolute change >= MATERIAL_CHANGE_THRESHOLD_PP, OR
        2. Direction reversal (rising -> falling or falling -> rising)
        """
        delta = current - previous
        
        # Rule 1: Large magnitude change
        if abs(delta) >= cls.MATERIAL_CHANGE_THRESHOLD_PP:
            return True
        
        # Rule 2: Direction reversal
        if cls._is_direction_reversal(current_direction, previous_direction):
            return True
        
        return False
    
    @classmethod
    def _is_direction_reversal(cls, current: str, previous: str) -> bool:
        """Check if direction reversed (rising <-> falling)."""
        reversals = {
            ("rising", "falling"),
            ("falling", "rising")
        }
        return (current, previous) in reversals or (previous, current) in reversals
    
    @classmethod
    def get_direction(cls, delta: float) -> str:
        """Determine direction from delta."""
        if delta > cls.DIRECTION_THRESHOLD_PP:
            return "rising"
        elif delta < -cls.DIRECTION_THRESHOLD_PP:
            return "falling"
        else:
            return "stable"
    
    @classmethod
    def get_direction_symbol(cls, direction: str) -> str:
        """Get arrow symbol for direction."""
        symbols = {
            "rising": "↑",
            "falling": "↓",
            "stable": "→"
        }
        return symbols.get(direction, "→")


# -----------------------------------------------------------------------------
# Data Structures
# -----------------------------------------------------------------------------

@dataclass
class CountrySnapshot:
    """Snapshot of a country's inflation data at a point in time."""
    code: str
    name: str
    yoy_inflation: float
    reference_period: str  # e.g., "2025-03"
    data_date: str  # e.g., "2025-01-27"

@dataclass
class WeeklySnapshot:
    """Complete weekly snapshot of all countries."""
    week_start: str  # Monday date, e.g., "2025-01-27"
    created_at: str
    countries: Dict[str, dict]  # code -> CountrySnapshot as dict

@dataclass
class CountryChange:
    """Detected change for a single country."""
    code: str
    name: str
    current_yoy: float
    previous_yoy: float
    delta_pp: float
    direction: str
    direction_symbol: str
    is_material: bool
    current_period: str
    previous_period: str


# -----------------------------------------------------------------------------
# Core Functions
# -----------------------------------------------------------------------------

def load_current_data() -> Dict:
    """Load current inflation data from historical_cpi.json."""
    with open(CURRENT_DATA_FILE, 'r') as f:
        return json.load(f)

def load_snapshots() -> List[Dict]:
    """Load existing weekly snapshots."""
    if os.path.exists(SNAPSHOTS_FILE):
        with open(SNAPSHOTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_snapshots(snapshots: List[Dict]) -> None:
    """Save weekly snapshots to file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SNAPSHOTS_FILE, 'w') as f:
        json.dump(snapshots, f, indent=2)

def get_week_start(date: datetime = None) -> str:
    """Get the Monday of the current week as YYYY-MM-DD."""
    if date is None:
        date = datetime.now()
    monday = date - timedelta(days=date.weekday())
    return monday.strftime("%Y-%m-%d")

def create_current_snapshot(data: Dict) -> WeeklySnapshot:
    """Create a snapshot from current data."""
    week_start = get_week_start()
    countries = {}
    
    for country_code, country_data in data.items():
        if not isinstance(country_data, dict):
            continue
        latest = country_data.get("latest")
        if latest and latest.get("value") is not None:
            countries[country_code] = {
                "code": country_code,
                "name": country_data.get("name", country_code),
                "yoy_inflation": latest["value"],
                "reference_period": latest["date"],
                "data_date": week_start
            }
    
    return WeeklySnapshot(
        week_start=week_start,
        created_at=datetime.now().isoformat(),
        countries=countries
    )

def get_previous_snapshot(snapshots: List[Dict]) -> Optional[Dict]:
    """Get the most recent previous snapshot."""
    if not snapshots:
        return None
    
    current_week = get_week_start()
    
    # Find the most recent snapshot that's not from this week
    for snapshot in reversed(snapshots):
        if snapshot.get("week_start") != current_week:
            return snapshot
    
    return None

def get_snapshot_before(snapshots: List[Dict], week_start: str) -> Optional[Dict]:
    """Get the most recent snapshot strictly older than week_start.

    Used to compute the *previous* week's delta, which is what direction-
    reversal detection compares against. week_start strings are YYYY-MM-DD,
    so lexicographic comparison is chronological.
    """
    for snapshot in reversed(snapshots):
        ws = snapshot.get("week_start")
        if ws and ws < week_start:
            return snapshot
    return None

def compare_snapshots(
    current: WeeklySnapshot,
    previous: Optional[Dict],
    before_previous: Optional[Dict] = None,
) -> List[CountryChange]:
    """Compare current snapshot with previous, detect changes.

    before_previous (the snapshot preceding `previous`) supplies the prior
    week's delta so direction reversals (rising -> falling and vice versa)
    can actually be detected.
    """
    changes = []
    
    for code, current_country in current.countries.items():
        current_yoy = current_country["yoy_inflation"]
        current_period = current_country["reference_period"]
        name = current_country["name"]
        
        # Get previous data
        if previous and code in previous.get("countries", {}):
            prev_country = previous["countries"][code]
            previous_yoy = prev_country["yoy_inflation"]
            previous_period = prev_country["reference_period"]
        else:
            # No previous data - treat as new
            previous_yoy = current_yoy
            previous_period = current_period
        
        # Calculate change
        delta = round(current_yoy - previous_yoy, 2)
        
        # Determine directions
        current_direction = ChangeRules.get_direction(delta)

        # Previous direction = last week's delta (previous vs the snapshot
        # before it). Without two weeks of history it stays "stable", which
        # makes the reversal rule a no-op for that country.
        previous_direction = "stable"
        if (
            previous and code in previous.get("countries", {})
            and before_previous and code in before_previous.get("countries", {})
        ):
            prior_yoy = before_previous["countries"][code]["yoy_inflation"]
            prev_delta = round(previous_yoy - prior_yoy, 2)
            previous_direction = ChangeRules.get_direction(prev_delta)
        
        # Check if material
        is_material = ChangeRules.is_material_change(
            current_yoy, previous_yoy,
            current_direction, previous_direction
        )
        
        changes.append(CountryChange(
            code=code,
            name=name,
            current_yoy=current_yoy,
            previous_yoy=previous_yoy,
            delta_pp=delta,
            direction=current_direction,
            direction_symbol=ChangeRules.get_direction_symbol(current_direction),
            is_material=is_material,
            current_period=current_period,
            previous_period=previous_period
        ))
    
    return changes

def format_change_line(change: CountryChange) -> str:
    """Format a single country change as a text line."""
    sign = "+" if change.delta_pp > 0 else ""
    return (
        f"  {change.name}: {change.current_yoy:.1f}% "
        f"({sign}{change.delta_pp:.1f}pp {change.direction_symbol}) "
        f"[{change.current_period}]"
    )


# -----------------------------------------------------------------------------
# Email Generation
# -----------------------------------------------------------------------------

def generate_email_subject(week_start: str, has_material_changes: bool) -> str:
    """Generate email subject line."""
    if has_material_changes:
        return f"Inflation Update — Week of {week_start}"
    else:
        return f"Inflation Update — Week of {week_start} (No Material Changes)"

def generate_email_body_text(
    week_start: str,
    changes: List[CountryChange],
    is_first_week: bool = False
) -> str:
    """Generate plain text email body."""
    
    material_changes = [c for c in changes if c.is_material]
    other_changes = [c for c in changes if not c.is_material]
    
    lines = []
    
    # Header
    lines.append(f"INFLATION UPDATE — Week of {week_start}")
    lines.append("=" * 50)
    lines.append("")
    
    # First week notice
    if is_first_week:
        lines.append("This is the first weekly snapshot. Changes will be")
        lines.append("reported starting next week.")
        lines.append("")
    
    # Summary
    if material_changes:
        lines.append(f"NOTABLE CHANGES THIS WEEK: {len(material_changes)}")
        lines.append("")
        for change in sorted(material_changes, key=lambda x: abs(x.delta_pp), reverse=True):
            lines.append(format_change_line(change))
        lines.append("")
    else:
        lines.append("NO MATERIAL CHANGES THIS WEEK")
        lines.append("")
        lines.append("All tracked economies showed inflation changes")
        lines.append("below the 0.3pp threshold with no direction reversals.")
        lines.append("")
    
    # Other updates (if any movement)
    minor_moves = [c for c in other_changes if c.delta_pp != 0]
    if minor_moves:
        lines.append("OTHER UPDATES (below threshold):")
        lines.append("")
        for change in sorted(minor_moves, key=lambda x: abs(x.delta_pp), reverse=True):
            lines.append(format_change_line(change))
        lines.append("")
    
    # Dashboard link
    lines.append("-" * 50)
    lines.append("")
    lines.append(f"Full dashboard: {DASHBOARD_URL}")
    lines.append("")
    
    # Footer
    lines.append("-" * 50)
    lines.append("No analysis. No predictions. Just the data.")
    lines.append("")
    lines.append("Material change threshold: ≥0.3pp or direction reversal")
    lines.append("Sources: Official government statistics agencies")
    lines.append("")
    lines.append("Some updates are compiled with AI assistance. Verify against the")
    lines.append("original official source before any formal or published use.")
    lines.append("")

    return "\n".join(lines)

def generate_email_body_html(
    week_start: str,
    changes: List[CountryChange],
    is_first_week: bool = False
) -> str:
    """Generate minimal HTML email body."""
    
    material_changes = [c for c in changes if c.is_material]
    other_changes = [c for c in changes if not c.is_material]
    
    html = []
    
    # Minimal inline styles
    html.append('''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               line-height: 1.5; color: #1f2937; max-width: 600px; margin: 0 auto; padding: 20px; }
        h1 { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
        h2 { font-size: 14px; font-weight: 600; color: #374151; margin: 20px 0 10px 0; 
             text-transform: uppercase; letter-spacing: 0.05em; }
        .summary { background: #f9fafb; padding: 16px; border-radius: 6px; margin: 16px 0; }
        .no-changes { color: #6b7280; }
        .change-item { margin: 8px 0; font-family: monospace; font-size: 13px; }
        .material { color: #dc2626; font-weight: 500; }
        .minor { color: #6b7280; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; 
                  font-size: 12px; color: #9ca3af; }
        .footer p { margin: 4px 0; }
        .principle { font-style: italic; color: #6b7280; }
        a { color: #2563eb; }
    </style>
</head>
<body>
''')
    
    html.append(f'<h1>Inflation Update — Week of {week_start}</h1>')
    
    # First week notice
    if is_first_week:
        html.append('<div class="summary">')
        html.append('<p>This is the first weekly snapshot. Changes will be reported starting next week.</p>')
        html.append('</div>')
    
    # Material changes
    if material_changes:
        html.append(f'<h2>Notable Changes ({len(material_changes)})</h2>')
        html.append('<div class="summary">')
        for change in sorted(material_changes, key=lambda x: abs(x.delta_pp), reverse=True):
            sign = "+" if change.delta_pp > 0 else ""
            html.append(
                f'<div class="change-item material">'
                f'{change.name}: {change.current_yoy:.1f}% '
                f'({sign}{change.delta_pp:.1f}pp {change.direction_symbol}) '
                f'<span style="color:#9ca3af">[{change.current_period}]</span>'
                f'</div>'
            )
        html.append('</div>')
    else:
        html.append('<div class="summary no-changes">')
        html.append('<p><strong>No material changes this week.</strong></p>')
        html.append('<p>All tracked economies showed inflation changes below the 0.3pp threshold with no direction reversals.</p>')
        html.append('</div>')
    
    # Minor changes
    minor_moves = [c for c in other_changes if c.delta_pp != 0]
    if minor_moves:
        html.append('<h2>Other Updates</h2>')
        for change in sorted(minor_moves, key=lambda x: abs(x.delta_pp), reverse=True):
            sign = "+" if change.delta_pp > 0 else ""
            html.append(
                f'<div class="change-item minor">'
                f'{change.name}: {change.current_yoy:.1f}% '
                f'({sign}{change.delta_pp:.1f}pp {change.direction_symbol}) '
                f'[{change.current_period}]'
                f'</div>'
            )
    
    # Dashboard link
    html.append(f'<p style="margin-top:24px"><a href="{DASHBOARD_URL}">View Full Dashboard →</a></p>')
    
    # Footer
    html.append('<div class="footer">')
    html.append('<p class="principle"><strong>No analysis. No predictions. Just the data.</strong></p>')
    html.append('<p>Material change threshold: ≥0.3pp or direction reversal</p>')
    html.append('<p>Sources: Official government statistics agencies</p>')
    html.append('<p>Some updates are compiled with AI assistance. Verify against the original official source before any formal or published use.</p>')
    html.append('</div>')
    
    html.append('</body></html>')
    
    return "\n".join(html)


# -----------------------------------------------------------------------------
# Email Sending
# -----------------------------------------------------------------------------

def send_email_resend(to_emails: List[str], subject: str, text_body: str, html_body: str) -> bool:
    """Send email using Resend API."""
    if not RESEND_API_KEY:
        print("Warning: RESEND_API_KEY not set, skipping email send")
        return False
    
    if not to_emails:
        print("Warning: No recipients configured, skipping email send")
        return False
    
    try:
        import requests
        
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": SENDER_EMAIL,
                "to": to_emails,
                "subject": subject,
                "text": text_body,
                "html": html_body
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Email sent successfully to {len(to_emails)} recipient(s)")
            return True
        else:
            print(f"❌ Email send failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Email send error: {e}")
        return False


# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

def run_weekly_alert(dry_run: bool = False) -> Dict:
    """
    Main function to run the weekly alert process.
    
    Args:
        dry_run: If True, generate report but don't send email or save snapshot
        
    Returns:
        Dict with execution results
    """
    print("=" * 60)
    print("WEEKLY INFLATION ALERT")
    print("=" * 60)
    print()
    
    # Load current data
    print("Loading current inflation data...")
    current_data = load_current_data()
    
    # Create current snapshot
    current_snapshot = create_current_snapshot(current_data)
    print(f"Week start: {current_snapshot.week_start}")
    print(f"Countries: {len(current_snapshot.countries)}")
    print()
    
    # Load previous snapshots
    print("Loading previous snapshots...")
    snapshots = load_snapshots()
    previous_snapshot = get_previous_snapshot(snapshots)
    
    is_first_week = previous_snapshot is None
    if is_first_week:
        print("No previous snapshot found - this is the first week")
    else:
        print(f"Previous snapshot: {previous_snapshot.get('week_start')}")
    print()
    
    # Compare and detect changes
    print("Comparing snapshots...")
    before_previous = (
        get_snapshot_before(snapshots, previous_snapshot["week_start"])
        if previous_snapshot else None
    )
    changes = compare_snapshots(current_snapshot, previous_snapshot, before_previous)
    
    material_changes = [c for c in changes if c.is_material]
    print(f"Material changes detected: {len(material_changes)}")
    print()
    
    # Generate email content
    print("Generating email content...")
    subject = generate_email_subject(current_snapshot.week_start, len(material_changes) > 0)
    text_body = generate_email_body_text(current_snapshot.week_start, changes, is_first_week)
    html_body = generate_email_body_html(current_snapshot.week_start, changes, is_first_week)
    
    print(f"Subject: {subject}")
    print()
    print("--- TEXT BODY ---")
    print(text_body)
    print("--- END TEXT BODY ---")
    print()
    
    # Save snapshot (unless dry run)
    if not dry_run:
        # Check if we already have a snapshot for this week
        existing_this_week = any(
            s.get("week_start") == current_snapshot.week_start 
            for s in snapshots
        )
        
        if not existing_this_week:
            print("Saving new snapshot...")
            snapshots.append(asdict(current_snapshot))
            save_snapshots(snapshots)
            print(f"Saved to {SNAPSHOTS_FILE}")
        else:
            print("Snapshot for this week already exists, skipping save")
        print()
    
    # Send email (unless dry run)
    email_sent = False
    if not dry_run:
        print("Sending email...")
        email_sent = send_email_resend(ALERT_RECIPIENTS, subject, text_body, html_body)
    else:
        print("Dry run - skipping email send")
    print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Week: {current_snapshot.week_start}")
    print(f"  Countries tracked: {len(current_snapshot.countries)}")
    print(f"  Material changes: {len(material_changes)}")
    print(f"  Email sent: {email_sent}")
    print(f"  Dry run: {dry_run}")
    print()
    
    return {
        "week_start": current_snapshot.week_start,
        "countries_tracked": len(current_snapshot.countries),
        "material_changes": len(material_changes),
        "changes": [asdict(c) for c in changes],
        "email_sent": email_sent,
        "is_first_week": is_first_week
    }


if __name__ == "__main__":
    import sys
    
    dry_run = "--dry-run" in sys.argv
    run_weekly_alert(dry_run=dry_run)
