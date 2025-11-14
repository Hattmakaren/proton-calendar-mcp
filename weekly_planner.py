#!/usr/bin/env python3
"""
Weekly Planner Agent
Analyzes the next month and suggests tasks for the upcoming week.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from server import fetch_calendar, filter_events_by_date_range
from trello_client import get_trello_client
from daily_summary import analyze_preparation_needs, format_time


def get_week_boundaries(start_date: datetime, weeks: int = 4) -> List[Tuple[datetime, datetime, int]]:
    """
    Calculate week boundaries for the next N weeks.

    Args:
        start_date: Starting date (usually today)
        weeks: Number of weeks to calculate

    Returns:
        List of tuples (week_start, week_end, week_number)
    """
    boundaries = []
    current = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    for i in range(weeks):
        week_start = current
        week_end = current + timedelta(days=7)
        boundaries.append((week_start, week_end, i + 1))
        current = week_end

    return boundaries


def group_by_week(items: List[Dict], week_boundaries: List[Tuple[datetime, datetime, int]],
                  date_key: str = 'start') -> Dict[int, List[Dict]]:
    """
    Group items by week number based on their date.

    Args:
        items: List of items (events or tasks) with date fields
        week_boundaries: List of week boundary tuples
        date_key: Key to access the date in each item

    Returns:
        Dictionary mapping week number to list of items
    """
    grouped = defaultdict(list)

    for item in items:
        item_date = item.get(date_key)
        if not item_date:
            continue

        # Convert to datetime if needed
        if not isinstance(item_date, datetime):
            item_date = datetime.combine(item_date, datetime.min.time())

        # Make timezone-naive for comparison
        if hasattr(item_date, 'tzinfo') and item_date.tzinfo is not None:
            item_date = item_date.replace(tzinfo=None)

        # Ensure week boundaries are also timezone-naive
        for week_start, week_end, week_num in week_boundaries:
            ws = week_start.replace(tzinfo=None) if hasattr(week_start, 'tzinfo') and week_start.tzinfo else week_start
            we = week_end.replace(tzinfo=None) if hasattr(week_end, 'tzinfo') and week_end.tzinfo else week_end

            if ws <= item_date < we:
                grouped[week_num].append(item)
                break

    return grouped


def calculate_daily_workload(events: List[Dict], day: datetime) -> Dict[str, any]:
    """
    Calculate workload metrics for a specific day.

    Args:
        events: List of calendar events
        day: Day to analyze

    Returns:
        Dictionary with workload metrics
    """
    day_start = day.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    day_end = day_start + timedelta(days=1)

    day_events = []
    for e in events:
        if e.get('start') and isinstance(e['start'], datetime):
            event_start = e['start']
            if hasattr(event_start, 'tzinfo') and event_start.tzinfo is not None:
                event_start = event_start.replace(tzinfo=None)
            if day_start <= event_start < day_end:
                day_events.append(e)

    total_events = len(day_events)
    total_hours = 0

    for event in day_events:
        if event.get('end') and isinstance(event['end'], datetime):
            event_start = event['start']
            event_end = event['end']
            if hasattr(event_start, 'tzinfo') and event_start.tzinfo is not None:
                event_start = event_start.replace(tzinfo=None)
            if hasattr(event_end, 'tzinfo') and event_end.tzinfo is not None:
                event_end = event_end.replace(tzinfo=None)
            duration = (event_end - event_start).total_seconds() / 3600
            total_hours += duration

    # Determine workload level
    if total_events == 0:
        level = "free"
    elif total_events <= 2 and total_hours <= 2:
        level = "light"
    elif total_events <= 4 and total_hours <= 4:
        level = "moderate"
    else:
        level = "busy"

    return {
        "date": day,
        "event_count": total_events,
        "total_hours": round(total_hours, 1),
        "level": level,
        "events": day_events
    }


def calculate_weekly_workload(events: List[Dict], week_start: datetime, week_end: datetime) -> Dict[str, any]:
    """
    Calculate workload for each day in a week.

    Args:
        events: List of calendar events
        week_start: Start of the week
        week_end: End of the week

    Returns:
        Dictionary with daily workload analysis
    """
    # Ensure timezone-naive comparisons
    ws = week_start.replace(tzinfo=None) if hasattr(week_start, 'tzinfo') and week_start.tzinfo else week_start
    we = week_end.replace(tzinfo=None) if hasattr(week_end, 'tzinfo') and week_end.tzinfo else week_end

    week_events = []
    for e in events:
        if e.get('start') and isinstance(e['start'], datetime):
            event_start = e['start']
            if hasattr(event_start, 'tzinfo') and event_start.tzinfo is not None:
                event_start = event_start.replace(tzinfo=None)
            if ws <= event_start < we:
                week_events.append(e)

    daily_workloads = []
    for i in range(7):
        day = ws + timedelta(days=i)
        workload = calculate_daily_workload(week_events, day)
        daily_workloads.append(workload)

    # Calculate week summary
    total_events = sum(d['event_count'] for d in daily_workloads)
    total_hours = sum(d['total_hours'] for d in daily_workloads)
    busy_days = sum(1 for d in daily_workloads if d['level'] in ['busy', 'moderate'])
    free_days = sum(1 for d in daily_workloads if d['level'] == 'free')

    return {
        "daily": daily_workloads,
        "total_events": total_events,
        "total_hours": round(total_hours, 1),
        "busy_days": busy_days,
        "free_days": free_days
    }


def suggest_weekly_tasks(overdue_cards: List[Dict], week_cards: List[Dict],
                        workload: Dict[str, any], max_tasks: int = 10) -> List[Dict]:
    """
    Intelligently suggest tasks for the week based on priorities and available time.

    Args:
        overdue_cards: List of overdue Trello cards
        week_cards: List of cards due this week
        workload: Weekly workload analysis
        max_tasks: Maximum number of tasks to suggest

    Returns:
        List of suggested tasks with priorities
    """
    suggestions = []
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Overdue tasks get highest priority
    for card in overdue_cards[:max_tasks]:
        if card.get('due_date'):
            card_due = card['due_date']
            if card_due.tzinfo is not None:
                card_due = card_due.replace(tzinfo=None)
            card_due = card_due.replace(hour=0, minute=0, second=0, microsecond=0)
            days_overdue = abs((now - card_due).days)

            suggestions.append({
                "card": card,
                "priority": "urgent",
                "reason": f"{days_overdue} days overdue"
            })

    # Add tasks due this week
    remaining = max_tasks - len(suggestions)
    for card in week_cards[:remaining]:
        if not card.get('due_date'):
            continue

        # Determine priority based on due date and workload
        card_date = card['due_date']
        if card_date.tzinfo is not None:
            card_date = card_date.replace(tzinfo=None)
        card_date = card_date.replace(hour=0, minute=0, second=0, microsecond=0)

        days_until = (card_date - now).days

        if days_until <= 2:
            priority = "high"
            reason = f"Due in {days_until} days"
        elif days_until <= 4:
            priority = "medium"
            reason = f"Due in {days_until} days"
        else:
            priority = "normal"
            reason = f"Due in {days_until} days"

        suggestions.append({
            "card": card,
            "priority": priority,
            "reason": reason
        })

    return suggestions


def format_monthly_overview(events_by_week: Dict[int, List[Dict]],
                            cards_by_week: Dict[int, List[Dict]],
                            week_boundaries: List[Tuple[datetime, datetime, int]]) -> str:
    """
    Format the monthly overview section with weekly grouping.

    Args:
        events_by_week: Events grouped by week number
        cards_by_week: Trello cards grouped by week number
        week_boundaries: Week boundary information

    Returns:
        Formatted string for monthly overview
    """
    lines = []
    lines.append("📅 MONTHLY OVERVIEW (Next 4 Weeks)")
    lines.append("=" * 60)
    lines.append("")

    for week_start, week_end, week_num in week_boundaries:
        week_events = events_by_week.get(week_num, [])
        week_cards = cards_by_week.get(week_num, [])

        week_end_display = week_end - timedelta(days=1)  # Show last day of week, not first day of next week
        lines.append(f"📆 Week {week_num}: {week_start.strftime('%b %d')} - {week_end_display.strftime('%b %d')}")
        lines.append("-" * 60)

        if week_events:
            lines.append(f"  📅 {len(week_events)} calendar event(s):")
            for event in week_events[:5]:  # Show up to 5 events
                event_date = event['start'].strftime('%a %b %d') if isinstance(event['start'], datetime) else str(event['start'])
                lines.append(f"     • {event['summary']} ({event_date})")
            if len(week_events) > 5:
                lines.append(f"     ... and {len(week_events) - 5} more")
        else:
            lines.append("  📅 No calendar events")

        lines.append("")

        if week_cards:
            lines.append(f"  📝 {len(week_cards)} Trello task(s) due:")
            for card in week_cards[:5]:  # Show up to 5 cards
                card_date = card['due_date'].strftime('%a %b %d') if card['due_date'] else 'No date'
                lines.append(f"     • {card['name']} ({card_date})")
            if len(week_cards) > 5:
                lines.append(f"     ... and {len(week_cards) - 5} more")
        else:
            lines.append("  📝 No Trello tasks due")

        lines.append("")

    return "\n".join(lines)


def format_weekly_focus(overdue_cards: List[Dict], week_events: List[Dict],
                       week_cards: List[Dict], suggested_tasks: List[Dict],
                       workload: Dict[str, any], week_start: datetime) -> str:
    """
    Format the weekly focus section with intelligent task suggestions.

    Args:
        overdue_cards: Overdue Trello cards
        week_events: Calendar events for the week
        week_cards: Trello cards due this week
        suggested_tasks: Intelligently suggested tasks
        workload: Weekly workload analysis
        week_start: Start of the week

    Returns:
        Formatted string for weekly focus
    """
    lines = []
    week_end = week_start + timedelta(days=7)
    week_end_display = week_end - timedelta(days=1)

    lines.append("=" * 60)
    lines.append("🎯 THIS WEEK'S FOCUS")
    lines.append(f"📆 {week_start.strftime('%A, %B %d')} - {week_end_display.strftime('%A, %B %d, %Y')}")
    lines.append("=" * 60)
    lines.append("")

    # Overdue tasks warning
    if overdue_cards:
        lines.append("⚠️  OVERDUE TASKS - URGENT ATTENTION NEEDED")
        lines.append("-" * 60)
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        for card in overdue_cards[:5]:  # Show top 5 overdue
            if card.get('due_date'):
                card_due = card['due_date']
                if card_due.tzinfo is not None:
                    card_due = card_due.replace(tzinfo=None)
                card_due = card_due.replace(hour=0, minute=0, second=0, microsecond=0)
                days_overdue = abs((now - card_due).days)

                lines.append(f"• {card['name']}")
                lines.append(f"  📋 {card['board_name']} → {card['list_name']}")
                lines.append(f"  ⚠️  {days_overdue} days overdue")
                lines.append(f"  🔗 {card['url']}")
                lines.append("")
        if len(overdue_cards) > 5:
            lines.append(f"... and {len(overdue_cards) - 5} more overdue tasks")
            lines.append("")
        lines.append("=" * 60)
        lines.append("")

    # Calendar events
    lines.append("📅 THIS WEEK'S SCHEDULE")
    lines.append("-" * 60)
    if week_events:
        # Group by day
        events_by_day = defaultdict(list)
        for event in week_events:
            event_date = event['start'].date() if isinstance(event['start'], datetime) else event['start']
            events_by_day[event_date].append(event)

        for day in sorted(events_by_day.keys()):
            day_name = day.strftime('%A, %B %d')
            lines.append(f"\n{day_name}:")
            for event in events_by_day[day]:
                start_time = format_time(event['start'])
                end_time = format_time(event['end']) if event['end'] else 'N/A'
                lines.append(f"  • {event['summary']}")
                lines.append(f"    ⏰ {start_time} - {end_time}")
                if event['location']:
                    lines.append(f"    📍 {event['location']}")

                # Add preparation suggestions for important events
                prep_items = analyze_preparation_needs(event)
                if prep_items:
                    lines.append("    🎯 Preparation:")
                    for item in prep_items[:2]:  # Show top 2 prep items
                        lines.append(f"       - {item}")

        lines.append(f"\n📊 Total: {len(week_events)} event(s) scheduled")
    else:
        lines.append("✨ No calendar events scheduled")
    lines.append("")
    lines.append("")

    # Suggested tasks
    lines.append("=" * 60)
    lines.append("✅ SUGGESTED WEEKLY TASKS")
    lines.append("-" * 60)
    if suggested_tasks:
        for suggestion in suggested_tasks:
            card = suggestion['card']
            priority = suggestion['priority']
            reason = suggestion['reason']

            # Priority emoji
            if priority == "urgent":
                priority_emoji = "🔴"
            elif priority == "high":
                priority_emoji = "🟠"
            elif priority == "medium":
                priority_emoji = "🟡"
            else:
                priority_emoji = "🟢"

            lines.append(f"{priority_emoji} {card['name']}")
            lines.append(f"  📋 {card['board_name']} → {card['list_name']}")
            lines.append(f"  📌 {reason}")
            if card['labels']:
                lines.append(f"  🏷️  {', '.join(card['labels'])}")
            if card['checklist_total'] > 0:
                lines.append(f"  ✓ Checklist: {card['checklist_completed']}/{card['checklist_total']}")
            lines.append(f"  🔗 {card['url']}")
            lines.append("")

        lines.append(f"📊 {len(suggested_tasks)} task(s) suggested for this week")
    else:
        lines.append("✨ No specific tasks suggested - your schedule looks clear!")
    lines.append("")

    return "\n".join(lines)


def format_planning_tips(workload: Dict[str, any], overdue_count: int) -> str:
    """
    Format planning tips based on workload analysis.

    Args:
        workload: Weekly workload analysis
        overdue_count: Number of overdue tasks

    Returns:
        Formatted string for planning tips
    """
    lines = []
    lines.append("=" * 60)
    lines.append("💡 PLANNING TIPS")
    lines.append("-" * 60)

    # Workload assessment
    if workload['busy_days'] >= 4:
        lines.append("⚠️  This is a BUSY week - prioritize ruthlessly!")
        lines.append("   Consider rescheduling non-urgent tasks")
    elif workload['busy_days'] >= 2:
        lines.append("📊 This is a MODERATE week - plan your time carefully")
        lines.append("   Focus on important tasks between meetings")
    else:
        lines.append("✨ This is a LIGHT week - great time for deep work!")
        lines.append("   Consider tackling larger projects or learning")

    lines.append("")

    # Overdue task warning
    if overdue_count > 0:
        lines.append(f"🚨 You have {overdue_count} overdue task(s) - prioritize these first!")
        lines.append("")

    # Free time optimization
    if workload['free_days'] > 0:
        lines.append(f"📅 You have {workload['free_days']} day(s) with no calendar events")
        lines.append("   Use these for focused work on important tasks")
        lines.append("")

    # General tips
    lines.append("📋 Review this plan at the start of each day")
    lines.append("✅ Update Trello cards as you complete tasks")
    lines.append("=" * 60)

    return "\n".join(lines)


async def generate_weekly_planner():
    """
    Generate a comprehensive weekly planner.

    Returns:
        Formatted weekly planner string
    """
    calendar_url = os.getenv("PROTON_CALENDAR_URL", "")

    if not calendar_url:
        return "❌ Error: PROTON_CALENDAR_URL environment variable is not set."

    # Initialize Trello client (optional)
    trello_client = get_trello_client()

    try:
        # Fetch calendar
        cal = await fetch_calendar(calendar_url)

        # Calculate date ranges
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        month_end = today + timedelta(days=28)  # 4 weeks
        week_end = today + timedelta(days=7)

        # Get week boundaries
        week_boundaries = get_week_boundaries(today, weeks=4)

        # Get all events for the month
        all_events = filter_events_by_date_range(cal, today, month_end)

        # Get events for this week
        week_events = filter_events_by_date_range(cal, today, week_end)

        # Fetch Trello cards if available
        overdue_cards = []
        week_cards = []
        all_cards = []

        if trello_client:
            try:
                overdue_cards = trello_client.get_overdue_cards()
                week_cards = trello_client.filter_cards_by_due_date(
                    trello_client.get_cards_from_boards(), today, week_end
                )
                all_cards = trello_client.get_cards_from_boards()
            except Exception as e:
                # Silently skip Trello if there's an error
                pass

        # Group events and cards by week
        events_by_week = group_by_week(all_events, week_boundaries, date_key='start')

        # Group Trello cards by week
        cards_with_dates = [c for c in all_cards if c.get('due_date')]
        cards_by_week = group_by_week(cards_with_dates, week_boundaries, date_key='due_date')

        # Calculate workload for this week
        week_start, _, _ = week_boundaries[0]
        workload = calculate_weekly_workload(all_events, week_start, week_end)

        # Suggest tasks for this week
        suggested_tasks = suggest_weekly_tasks(overdue_cards, week_cards, workload)

        # Build the full planner output
        lines = []
        lines.append("=" * 60)
        lines.append("📋 WEEKLY PLANNER")
        lines.append(f"🗓️  Generated: {today.strftime('%A, %B %d, %Y')}")
        lines.append("=" * 60)
        lines.append("")

        # Monthly overview
        lines.append(format_monthly_overview(events_by_week, cards_by_week, week_boundaries))
        lines.append("")

        # Weekly focus
        lines.append(format_weekly_focus(overdue_cards, week_events, week_cards,
                                        suggested_tasks, workload, week_start))
        lines.append("")

        # Planning tips
        lines.append(format_planning_tips(workload, len(overdue_cards)))

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Error generating weekly planner: {str(e)}"


async def main():
    """Main entry point."""
    import sys

    # Fix encoding for Windows console
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    planner = await generate_weekly_planner()
    print(planner)


if __name__ == "__main__":
    asyncio.run(main())
