#!/usr/bin/env python3
"""
Daily Summary Agent
Provides a summary of today's events and preparation needed for tomorrow.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from server import fetch_calendar, filter_events_by_date_range
from trello_client import get_trello_client


def analyze_preparation_needs(event: Dict) -> List[str]:
    """
    Analyze an event and determine what preparation might be needed.

    Args:
        event: Event dictionary with details

    Returns:
        List of preparation suggestions
    """
    preparations = []

    summary = event["summary"].lower()
    description = event["description"].lower()
    location = event["location"].lower()

    # Check for meetings
    if any(word in summary for word in ["meeting", "call", "sync", "standup", "review"]):
        preparations.append("Review agenda and prepare talking points")

    # Check for presentations
    if any(word in summary for word in ["presentation", "demo", "showcase"]):
        preparations.append("Prepare slides and test equipment")
        preparations.append("Practice presentation")

    # Check for interviews
    if any(word in summary for word in ["interview", "candidate"]):
        preparations.append("Review candidate resume")
        preparations.append("Prepare interview questions")

    # Check for location-based preparation
    if location and location != "":
        if any(word in location for word in ["conference", "office", "building"]):
            preparations.append(f"Check directions to {event['location']}")
        if "room" in location:
            preparations.append("Book/confirm room availability")

    # Check for project-related events
    if any(word in summary for word in ["project", "milestone", "deadline", "delivery"]):
        preparations.append("Review project status and deliverables")

    # Check for training/workshop
    if any(word in summary for word in ["training", "workshop", "seminar", "course"]):
        preparations.append("Review course materials")
        preparations.append("Prepare questions or topics to discuss")

    # Check description for specific requirements
    if "bring" in description or "prepare" in description:
        preparations.append("Check event description for specific requirements")

    return preparations


def format_time(dt) -> str:
    """Format datetime for display."""
    if isinstance(dt, datetime):
        return dt.strftime("%I:%M %p")
    return str(dt)


def format_event_summary(event: Dict, show_prep: bool = False) -> str:
    """
    Format a single event for display.

    Args:
        event: Event dictionary
        show_prep: Whether to include preparation suggestions

    Returns:
        Formatted event string
    """
    lines = []

    # Event title and time
    start_time = format_time(event["start"])
    end_time = format_time(event["end"]) if event["end"] else "N/A"
    lines.append(f"• {event['summary']}")
    lines.append(f"  ⏰ {start_time} - {end_time}")

    # Location
    if event["location"]:
        lines.append(f"  📍 {event['location']}")

    # Description
    if event["description"]:
        # Limit description to first line or 100 chars
        desc = event["description"]
        if len(desc) > 100:
            desc = desc[:97] + "..."
        if "\n" in desc:
            desc = desc.split("\n")[0]
        lines.append(f"  📝 {desc}")

    # Preparation suggestions
    if show_prep:
        prep_items = analyze_preparation_needs(event)
        if prep_items:
            lines.append("  🎯 Preparation needed:")
            for item in prep_items:
                lines.append(f"     - {item}")

    return "\n".join(lines)


def format_trello_card(card: Dict, show_overdue: bool = False) -> str:
    """
    Format a single Trello card for display.

    Args:
        card: Card dictionary from Trello
        show_overdue: Whether to show overdue information

    Returns:
        Formatted card string
    """
    lines = []

    # Card title and board
    lines.append(f"• {card['name']}")
    lines.append(f"  📋 {card['board_name']} → {card['list_name']}")

    # Due date
    if card['due_date']:
        due_time = card['due_date'].strftime("%I:%M %p")
        if show_overdue:
            now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            card_due = card['due_date'].replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
            days_overdue = (now - card_due).days
            lines.append(f"  ⏰ Due: {card['due_date'].strftime('%Y-%m-%d')} {due_time} ({days_overdue} days overdue)")
        else:
            lines.append(f"  ⏰ Due: {due_time}")

    # Labels
    if card['labels']:
        labels_str = ", ".join(card['labels'])
        lines.append(f"  🏷️  {labels_str}")

    # Checklist progress
    if card['checklist_total'] > 0:
        progress = f"{card['checklist_completed']}/{card['checklist_total']}"
        lines.append(f"  ✓ Checklist: {progress}")

    # Description (truncated)
    if card['description']:
        desc = card['description']
        if len(desc) > 100:
            desc = desc[:97] + "..."
        if "\n" in desc:
            desc = desc.split("\n")[0]
        lines.append(f"  📝 {desc}")

    # URL
    lines.append(f"  🔗 {card['url']}")

    return "\n".join(lines)


async def generate_daily_summary():
    """
    Generate a comprehensive daily summary.

    Returns:
        Formatted summary string
    """
    calendar_url = os.getenv("PROTON_CALENDAR_URL", "")

    if not calendar_url:
        return "❌ Error: PROTON_CALENDAR_URL environment variable is not set."

    # Initialize Trello client (optional)
    trello_client = get_trello_client()

    try:
        # Fetch calendar
        cal = await fetch_calendar(calendar_url)

        # Get today's events
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        today_events = filter_events_by_date_range(cal, today_start, today_end)

        # Get tomorrow's events
        tomorrow_start = today_end
        tomorrow_end = tomorrow_start + timedelta(days=1)
        tomorrow_events = filter_events_by_date_range(cal, tomorrow_start, tomorrow_end)

        # Fetch Trello cards if client is available
        overdue_cards = []
        today_cards = []
        tomorrow_cards = []
        if trello_client:
            try:
                overdue_cards = trello_client.get_overdue_cards()
                today_cards = trello_client.get_cards_due_today()
                tomorrow_cards = trello_client.get_cards_due_tomorrow()
            except Exception as e:
                # Silently skip Trello if there's an error
                pass

        # Build summary
        lines = []
        lines.append("=" * 60)
        lines.append("📅 DAILY SUMMARY")
        lines.append(f"🗓️  {today_start.strftime('%A, %B %d, %Y')}")
        lines.append("=" * 60)
        lines.append("")

        # Overdue Trello cards
        if overdue_cards:
            lines.append("⚠️  OVERDUE TASKS")
            lines.append("-" * 60)
            for card in overdue_cards:
                lines.append(format_trello_card(card, show_overdue=True))
                lines.append("")
            lines.append(f"📊 You have {len(overdue_cards)} overdue task(s) - prioritize these!")
            lines.append("")
            lines.append("=" * 60)
            lines.append("")

        # Today's schedule
        lines.append("🌟 TODAY'S SCHEDULE")
        lines.append("-" * 60)
        if today_events:
            for event in today_events:
                lines.append(format_event_summary(event))
                lines.append("")

            # Summary stats
            lines.append(f"📊 You have {len(today_events)} event(s) scheduled today")
            lines.append("")
        else:
            lines.append("✨ No events scheduled for today!")
            lines.append("")

        # Today's Trello cards
        if today_cards:
            lines.append("-" * 60)
            lines.append("📝 TODAY'S TASKS (Trello)")
            lines.append("-" * 60)
            for card in today_cards:
                lines.append(format_trello_card(card))
                lines.append("")
            lines.append(f"📊 You have {len(today_cards)} task(s) due today")
            lines.append("")

        # Tomorrow's preparation
        if tomorrow_events:
            lines.append("=" * 60)
            lines.append("🔮 PREPARE FOR TOMORROW")
            lines.append(f"📆 {tomorrow_start.strftime('%A, %B %d, %Y')}")
            lines.append("-" * 60)

            for event in tomorrow_events:
                lines.append(format_event_summary(event, show_prep=True))
                lines.append("")

            lines.append(f"📊 You have {len(tomorrow_events)} event(s) tomorrow")
            lines.append("")
        else:
            lines.append("=" * 60)
            lines.append("🔮 TOMORROW")
            lines.append("-" * 60)
            lines.append("✨ No events scheduled for tomorrow")
            lines.append("")

        # Tomorrow's Trello cards
        if tomorrow_cards:
            lines.append("-" * 60)
            lines.append("📝 TOMORROW'S TASKS (Trello)")
            lines.append("-" * 60)
            for card in tomorrow_cards:
                lines.append(format_trello_card(card))
                lines.append("")
            lines.append(f"📊 You have {len(tomorrow_cards)} task(s) due tomorrow")
            lines.append("")

        # General tips
        lines.append("=" * 60)
        lines.append("💡 TIPS")
        lines.append("-" * 60)

        if overdue_cards:
            lines.append("🚨 You have overdue tasks - prioritize completing these first!")

        if today_events:
            # Check for early morning events
            early_events = [e for e in today_events if isinstance(e["start"], datetime) and e["start"].hour < 9]
            if early_events:
                lines.append("⏰ You have early morning event(s) - set an alarm!")

            # Check for back-to-back events
            if len(today_events) > 1:
                for i in range(len(today_events) - 1):
                    if isinstance(today_events[i]["end"], datetime) and isinstance(today_events[i+1]["start"], datetime):
                        gap = (today_events[i+1]["start"] - today_events[i]["end"]).total_seconds() / 60
                        if gap < 15:
                            lines.append("⚠️  You have back-to-back events - consider breaks!")
                            break

        if tomorrow_events:
            lines.append("📋 Review tomorrow's schedule tonight")

        lines.append("💧 Stay hydrated and take breaks!")
        lines.append("=" * 60)

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Error generating summary: {str(e)}"


async def main():
    """Main entry point."""
    import sys

    # Fix encoding for Windows console
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    summary = await generate_daily_summary()
    print(summary)


if __name__ == "__main__":
    asyncio.run(main())
