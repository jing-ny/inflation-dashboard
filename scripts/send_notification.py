#!/usr/bin/env python3
"""
Send email notifications for inflation dashboard updates.
Uses Resend API for email delivery.
"""

import json
import os
import sys
import argparse
from datetime import datetime
import requests

RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
NOTIFICATION_EMAIL = os.environ.get('NOTIFICATION_EMAIL')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'Inflation Dashboard <updates@resend.dev>')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_summary():
    """Load the monitor summary from the last run"""
    # Must match the path monitor_updates.py writes (repo-root data/, an
    # ephemeral run artifact — deliberately outside the committed docs/data/).
    summary_path = os.path.join(BASE_DIR, 'data/monitor_summary.json')
    if os.path.exists(summary_path):
        with open(summary_path, 'r') as f:
            return json.load(f)
    return None


def format_html_email(summary, status, has_changes):
    """Format the email as HTML"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
    
    # Determine overall status
    if status == 'failure':
        status_emoji = '❌'
        status_text = 'Monitoring Failed'
        status_color = '#dc2626'
    elif summary and summary.get('errors'):
        status_emoji = '⚠️'
        status_text = 'Completed with Errors'
        status_color = '#f59e0b'
    elif has_changes == 'true':
        status_emoji = '✅'
        status_text = 'Data Updated'
        status_color = '#10b981'
    else:
        status_emoji = '✨'
        status_text = 'No Changes'
        status_color = '#6b7280'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #374151; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: {status_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px; }}
            .section {{ margin: 15px 0; padding: 15px; background: white; border-radius: 6px; border: 1px solid #e5e7eb; }}
            .section h3 {{ margin: 0 0 10px 0; color: #1f2937; }}
            .item {{ padding: 8px 0; border-bottom: 1px solid #f3f4f6; }}
            .item:last-child {{ border-bottom: none; }}
            .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }}
            .badge-update {{ background: #dcfce7; color: #166534; }}
            .badge-alert {{ background: #fef3c7; color: #92400e; }}
            .badge-error {{ background: #fee2e2; color: #991b1b; }}
            .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; }}
            a {{ color: #2563eb; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; font-size: 24px;">{status_emoji} Inflation Dashboard: {status_text}</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">{timestamp}</p>
            </div>
            <div class="content">
    """
    
    if summary:
        # Updates section
        if summary.get('updates'):
            html += """
                <div class="section">
                    <h3>📊 Data Updates</h3>
            """
            for update in summary['updates']:
                html += f"""
                    <div class="item">
                        <span class="badge badge-update">UPDATED</span>
                        <strong>{update['country']}</strong>: {update['old_date']} → {update['new_date']}
                        <br><small>New value: {update['new_value']}%</small>
                    </div>
                """
            html += "</div>"
        
        # Alerts section
        if summary.get('alerts'):
            html += """
                <div class="section">
                    <h3>⚠️ Alerts - Action May Be Needed</h3>
            """
            for alert in summary['alerts']:
                if alert['type'] == 'STALE_DATA':
                    html += f"""
                        <div class="item">
                            <span class="badge badge-alert">STALE</span>
                            <strong>{alert['country']}</strong>: Data is {alert['days_old']} days old
                            <br><small>Last update: {alert['last_update']} - Check official source for newer data</small>
                        </div>
                    """
                elif alert['type'] in ['CB_MEETING_RECENT', 'CB_MEETING_UPCOMING']:
                    html += f"""
                        <div class="item">
                            <span class="badge badge-alert">CB MEETING</span>
                            <strong>{alert['country']} ({alert['bank']})</strong>
                            <br><small>{alert['message']}</small>
                        </div>
                    """
                elif alert['type'] == 'IMF_WEO_RELEASE':
                    html += f"""
                        <div class="item">
                            <span class="badge badge-alert">IMF WEO</span>
                            <strong>World Economic Outlook</strong>
                            <br><small>{alert['message']}</small>
                        </div>
                    """
            html += "</div>"
        
        # Errors section
        if summary.get('errors'):
            html += """
                <div class="section">
                    <h3>❌ Errors</h3>
            """
            for error in summary['errors']:
                html += f"""
                    <div class="item">
                        <span class="badge badge-error">ERROR</span>
                        {error}
                    </div>
                """
            html += "</div>"
        
        # No issues
        if not summary.get('updates') and not summary.get('alerts') and not summary.get('errors'):
            html += """
                <div class="section">
                    <h3>✨ All Good!</h3>
                    <p>All data is up to date. No action needed.</p>
                </div>
            """
    else:
        html += """
            <div class="section">
                <h3>No Summary Available</h3>
                <p>The monitoring script did not produce a summary. Check the workflow logs.</p>
            </div>
        """
    
    html += f"""
                <div class="footer">
                    <p>
                        <a href="https://jing-ny.github.io/inflation-dashboard/">View Dashboard</a> · 
                        <a href="https://github.com/jing-ny/inflation-dashboard/actions">View Workflow Runs</a>
                    </p>
                    <p>This is an automated message from your Inflation Dashboard.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def send_email(subject, html_content):
    """Send email via Resend API"""
    
    if not RESEND_API_KEY:
        print("WARNING: RESEND_API_KEY not set. Email not sent.")
        print(f"\nEmail would have been sent to: {NOTIFICATION_EMAIL}")
        print(f"Subject: {subject}")
        return False
    
    if not NOTIFICATION_EMAIL:
        print("WARNING: NOTIFICATION_EMAIL not set. Email not sent.")
        return False
    
    try:
        response = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {RESEND_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'from': FROM_EMAIL,
                'to': [NOTIFICATION_EMAIL],
                'subject': subject,
                'html': html_content
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"Email sent successfully to {NOTIFICATION_EMAIL}")
            return True
        else:
            print(f"ERROR sending email: {response.status_code} - {response.text}")
            return False
        
    except Exception as e:
        print(f"ERROR sending email: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Send notification email')
    parser.add_argument('--status', default='success', help='Workflow status (success/failure)')
    parser.add_argument('--changes', default='false', help='Whether changes were made (true/false)')
    args = parser.parse_args()
    
    # Load summary
    summary = load_summary()
    
    # Skip email if no updates/alerts (optional - comment out to always send)
    if args.status == 'success' and args.changes == 'false':
        if not summary or (not summary.get('alerts') and not summary.get('errors')):
            print("No updates or alerts. Skipping email.")
            return
    
    # Determine subject line
    if args.status == 'failure':
        subject = "❌ Inflation Dashboard: Monitoring Failed"
    elif summary and summary.get('errors'):
        subject = "⚠️ Inflation Dashboard: Completed with Errors"
    elif summary and summary.get('alerts'):
        alert_count = len(summary['alerts'])
        subject = f"⚠️ Inflation Dashboard: {alert_count} Alert(s) - Action Needed"
    elif args.changes == 'true':
        update_count = len(summary.get('updates', [])) if summary else 0
        subject = f"✅ Inflation Dashboard: {update_count} Update(s) Applied"
    else:
        subject = "✨ Inflation Dashboard: All Up to Date"
    
    # Format and send email
    html_content = format_html_email(summary, args.status, args.changes)
    send_email(subject, html_content)


if __name__ == '__main__':
    main()
