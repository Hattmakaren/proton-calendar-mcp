#!/usr/bin/env python3
"""
Proton Calendar MCP Server
Fetches calendar data from a read-only Proton Calendar URL and exposes it via MCP.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlparse

import httpx
from icalendar import Calendar
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# Initialize the MCP server
app = Server("proton-calendar-server")

# Global variable to store the calendar URL
CALENDAR_URL = os.getenv("PROTON_CALENDAR_URL", "")


async def fetch_calendar(url: str) -> Calendar:
    """
    Fetch and parse the iCalendar data from the provided URL.

    Args:
        url: The calendar URL to fetch from

    Returns:
        Parsed Calendar object

    Raises:
        httpx.HTTPError: If the HTTP request fails
        ValueError: If the calendar data cannot be parsed
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()

        try:
            return Calendar.from_ical(response.content)
        except Exception as e:
            raise ValueError(f"Failed to parse calendar data: {str(e)}")


def format_event(event) -> dict:
    """
    Extract and format relevant information from a calendar event.

    Args:
        event: iCalendar event component

    Returns:
        Dictionary with formatted event data
    """
    return {
        "summary": str(event.get("summary", "No Title")),
        "description": str(event.get("description", "")),
        "location": str(event.get("location", "")),
        "start": event.get("dtstart").dt if event.get("dtstart") else None,
        "end": event.get("dtend").dt if event.get("dtend") else None,
        "status": str(event.get("status", "")),
        "uid": str(event.get("uid", "")),
    }


def filter_events_by_date_range(
    cal: Calendar,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[dict]:
    """
    Filter calendar events by date range.

    Args:
        cal: Parsed Calendar object
        start_date: Optional start date for filtering (inclusive)
        end_date: Optional end date for filtering (inclusive)

    Returns:
        List of filtered and formatted events sorted by start time
    """
    events = []

    for component in cal.walk("VEVENT"):
        event = format_event(component)
        event_start = event["start"]

        if event_start is None:
            continue

        # Convert to datetime if it's a date
        if not isinstance(event_start, datetime):
            event_start = datetime.combine(event_start, datetime.min.time())

        # Make timezone-naive for comparison
        if event_start.tzinfo is not None:
            event_start = event_start.replace(tzinfo=None)

        # Filter by date range
        if start_date and event_start < start_date:
            continue
        if end_date and event_start > end_date:
            continue

        events.append(event)

    # Sort events by start time
    events.sort(key=lambda x: x["start"] if x["start"] else datetime.min)
    return events


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="get_today_events",
            description="Get all calendar events for today from your Proton Calendar",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_week_events",
            description="Get all calendar events for the upcoming week (7 days) from your Proton Calendar",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_date_range_events",
            description="Get calendar events for a specific date range from your Proton Calendar",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format",
                    },
                },
                "required": ["start_date", "end_date"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    if not CALENDAR_URL:
        return [
            TextContent(
                type="text",
                text="Error: PROTON_CALENDAR_URL environment variable is not set. "
                     "Please set it to your Proton Calendar's read-only share URL.",
            )
        ]

    try:
        cal = await fetch_calendar(CALENDAR_URL)

        if name == "get_today_events":
            now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = now + timedelta(days=1)
            events = filter_events_by_date_range(cal, now, tomorrow)

            if not events:
                return [TextContent(type="text", text="No events scheduled for today.")]

            result = "Events for Today:\n\n"
            for event in events:
                start_time = event["start"].strftime("%I:%M %p") if isinstance(event["start"], datetime) else str(event["start"])
                result += f"• {event['summary']}\n"
                result += f"  Time: {start_time}\n"
                if event["location"]:
                    result += f"  Location: {event['location']}\n"
                if event["description"]:
                    result += f"  Description: {event['description']}\n"
                result += "\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_week_events":
            now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            week_end = now + timedelta(days=7)
            events = filter_events_by_date_range(cal, now, week_end)

            if not events:
                return [TextContent(type="text", text="No events scheduled for the next 7 days.")]

            result = "Events for the Next Week:\n\n"
            current_date = None
            for event in events:
                event_date = event["start"].date() if isinstance(event["start"], datetime) else event["start"]

                if event_date != current_date:
                    current_date = event_date
                    result += f"\n{current_date.strftime('%A, %B %d, %Y')}:\n"

                start_time = event["start"].strftime("%I:%M %p") if isinstance(event["start"], datetime) else "All day"
                result += f"  • {event['summary']} ({start_time})\n"
                if event["location"]:
                    result += f"    Location: {event['location']}\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_date_range_events":
            start_date = datetime.strptime(arguments["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(arguments["end_date"], "%Y-%m-%d")
            end_date = end_date.replace(hour=23, minute=59, second=59)

            events = filter_events_by_date_range(cal, start_date, end_date)

            if not events:
                return [TextContent(type="text", text=f"No events scheduled between {arguments['start_date']} and {arguments['end_date']}.")]

            result = f"Events from {arguments['start_date']} to {arguments['end_date']}:\n\n"
            current_date = None
            for event in events:
                event_date = event["start"].date() if isinstance(event["start"], datetime) else event["start"]

                if event_date != current_date:
                    current_date = event_date
                    result += f"\n{current_date.strftime('%A, %B %d, %Y')}:\n"

                start_time = event["start"].strftime("%I:%M %p") if isinstance(event["start"], datetime) else "All day"
                result += f"  • {event['summary']} ({start_time})\n"
                if event["location"]:
                    result += f"    Location: {event['location']}\n"
                if event["description"]:
                    result += f"    Description: {event['description']}\n"

            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error fetching calendar: {str(e)}")]


async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
