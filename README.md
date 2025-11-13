# Proton Calendar MCP Server

An MCP (Model Context Protocol) server that provides read-only access to your Proton Calendar data for AI assistants like Claude Code.

## Features

- **Read-only access** to your Proton Calendar via shareable URL
- **Three tools** for querying calendar events:
  - `get_today_events`: Get all events scheduled for today
  - `get_week_events`: Get all events for the next 7 days
  - `get_date_range_events`: Get events for a custom date range
- **Comprehensive tests** to ensure reliable calendar data fetching

## Prerequisites

- Python 3.8 or higher (tested with Python 3.13)
- A Proton Calendar account
- A shareable calendar URL from Proton Calendar (read-only)

## Setup Instructions

### 1. Get Your Proton Calendar Share URL

1. Go to [calendar.proton.me](https://calendar.proton.me)
2. Select the calendar you want to share
3. Click on the calendar settings (three dots menu)
4. Select "Share" or "Get shareable link"
5. Generate a **read-only** URL for your calendar
6. Copy the URL (it should be in .ics format)

### 2. Install Dependencies

```bash
cd proton-calendar-mcp
pip install -r requirements.txt
```

### 3. Set Environment Variable

Set the `PROTON_CALENDAR_URL` environment variable to your calendar's share URL:

**Windows (PowerShell):**
```powershell
$env:PROTON_CALENDAR_URL="https://calendar.proton.me/api/calendar/v1/url/YOUR_CALENDAR_ID/calendar.ics"
```

**Windows (Command Prompt):**
```cmd
set PROTON_CALENDAR_URL=https://calendar.proton.me/api/calendar/v1/url/YOUR_CALENDAR_ID/calendar.ics
```

**Linux/Mac:**
```bash
export PROTON_CALENDAR_URL="https://calendar.proton.me/api/calendar/v1/url/YOUR_CALENDAR_ID/calendar.ics"
```

### 4. Register with Claude Code

Register the MCP server with Claude Code using stdio transport:

```bash
claude mcp add --transport stdio proton-calendar --env PROTON_CALENDAR_URL="YOUR_URL_HERE" -- python C:\Users\jocku\OneDrive\Projects\Claude\test-agents\proton-calendar-mcp\server.py
```

**Important:**
- Replace `YOUR_URL_HERE` with your actual Proton Calendar URL
- Update the path to match where you saved `server.py`
- For Linux/Mac, use forward slashes in the path

**Alternative:** Set the environment variable system-wide, then register without the `--env` flag:

```bash
claude mcp add --transport stdio proton-calendar -- python /path/to/server.py
```

### 5. Verify Installation

Check that the server is registered and connected:

```bash
claude mcp list
```

You should see:
```
proton-calendar: python /path/to/server.py - ✓ Connected
```

## Usage

### Using with Claude Code

Once configured, you can ask Claude Code to:

- "What's on my calendar today?"
- "Show me my schedule for the next week"
- "What events do I have between January 15 and January 20?"

Claude Code will use the appropriate tool to fetch and display your calendar events.

### Daily Summary Agent

The project includes a **daily summary agent** that provides an intelligent overview of your day:

```bash
cd proton-calendar-mcp
python daily_summary.py
```

**Features:**
- 📅 Shows today's complete schedule
- 🔮 Previews tomorrow's events
- 🎯 Suggests preparation needed for tomorrow's meetings
- 💡 Provides helpful tips (early morning alerts, back-to-back meeting warnings)
- ⏰ Highlights important scheduling considerations

**Example output:**
```
============================================================
📅 DAILY SUMMARY
🗓️  Thursday, November 13, 2025
============================================================

🌟 TODAY'S SCHEDULE
------------------------------------------------------------
• Team Meeting
  ⏰ 02:00 PM - 03:00 PM
  📍 Conference Room A
  📝 Weekly sync meeting

📊 You have 1 event(s) scheduled today

============================================================
🔮 PREPARE FOR TOMORROW
📆 Friday, November 14, 2025
------------------------------------------------------------
• Product Demo
  ⏰ 10:00 AM - 11:00 AM
  📍 Main Office
  📝 Demo new features to stakeholders
  🎯 Preparation needed:
     - Prepare slides and test equipment
     - Practice presentation
     - Review agenda and prepare talking points

📊 You have 1 event(s) tomorrow

============================================================
💡 TIPS
------------------------------------------------------------
📋 Review tomorrow's schedule tonight
💧 Stay hydrated and take breaks!
============================================================
```

**Intelligent preparation suggestions:**

The agent analyzes your events and provides context-aware preparation suggestions:
- **Meetings** → Review agenda and prepare talking points
- **Presentations** → Prepare slides, test equipment, practice
- **Interviews** → Review resumes, prepare questions
- **Training** → Review materials, prepare questions
- **Travel required** → Check directions, book rooms

**Automation tip:** You can schedule this to run automatically:
- **Windows:** Use Task Scheduler
- **Linux/Mac:** Use cron job

Example cron entry (run daily at 7 AM):
```bash
0 7 * * * cd /path/to/proton-calendar-mcp && python daily_summary.py
```

## Available Tools

### get_today_events
Returns all events scheduled for today.

**No parameters required**

**Example output:**
```
Events for Today:

• Test Meeting
  Time: 02:00 PM
  Location: Conference Room A
  Description: This is a test meeting

• Team Standup
  Time: 10:00 AM
  Location: Office
```

### get_week_events
Returns all events scheduled for the next 7 days, grouped by date.

**No parameters required**

**Example output:**
```
Events for the Next Week:

Wednesday, November 13, 2025:
  • Test Meeting (02:00 PM)
    Location: Conference Room A

Thursday, November 14, 2025:
  • Team Standup (10:00 AM)
    Location: Office
```

### get_date_range_events
Returns events within a specified date range.

**Parameters:**
- `start_date` (string): Start date in YYYY-MM-DD format
- `end_date` (string): End date in YYYY-MM-DD format

**Example output:**
```
Events from 2025-11-13 to 2025-11-20:

Wednesday, November 13, 2025:
  • Test Meeting (02:00 PM)
    Location: Conference Room A
    Description: This is a test meeting
```

## Testing

Run the test suite to verify the calendar fetching functionality:

```bash
cd proton-calendar-mcp
pytest tests/ -v
```

All tests should pass:
```
23 passed in 2.17s
```

### Test Coverage

The test suite includes:

**Calendar Fetching Tests:**
- ✅ Successful calendar fetching
- ✅ HTTP error handling
- ✅ Invalid data handling
- ✅ Timeout handling
- ✅ Event formatting
- ✅ Date range filtering
- ✅ Today's events filtering
- ✅ Event sorting
- ✅ All-day event handling

**Daily Summary Agent Tests:**
- ✅ Preparation analysis for meetings
- ✅ Preparation analysis for presentations
- ✅ Preparation analysis for interviews
- ✅ Location-based preparation
- ✅ Training event preparation
- ✅ Time formatting
- ✅ Event summary formatting
- ✅ Long description handling
- ✅ Multiline description handling

## Architecture

### Components

**MCP Server (server.py):**
1. **fetch_calendar()**: Async function to fetch and parse iCalendar data from URL
2. **format_event()**: Extracts relevant information from calendar events
3. **filter_events_by_date_range()**: Filters and sorts events by date
4. **MCP Server**: Exposes three tools via the Model Context Protocol

**Daily Summary Agent (daily_summary.py):**
1. **generate_daily_summary()**: Creates comprehensive daily overview
2. **analyze_preparation_needs()**: Intelligent preparation suggestions
3. **format_event_summary()**: User-friendly event formatting
4. **Smart tips**: Early morning alerts, back-to-back meeting warnings

### Dependencies

- `mcp>=1.0.0` - Official Model Context Protocol SDK
- `icalendar>=6.0.0` - RFC 5545 compliant iCalendar parser
- `httpx>=0.27.0` - Modern async HTTP client
- `pytest>=8.0.0` - Testing framework
- `pytest-asyncio>=0.23.0` - Async support for pytest

## Security & Privacy

- This server only has **read-only** access to your calendar
- Your calendar URL should be kept private (it's a secret URL)
- The MCP server runs locally on your machine
- No data is sent to third-party services except Proton's servers to fetch your calendar
- The calendar URL is passed via environment variable for security

## Troubleshooting

### "PROTON_CALENDAR_URL environment variable is not set"
Make sure you've set the environment variable before running the server or registering it with Claude Code. You can either:
1. Set it system-wide in your shell
2. Pass it via `--env` flag when registering with `claude mcp add`

### "Error fetching calendar: [HTTP error]"
- Verify your calendar URL is correct
- Check that the URL is publicly accessible (test it in a browser)
- Ensure you have internet connectivity
- Make sure the calendar URL hasn't expired

### Events not showing up
- Verify events exist in your Proton Calendar for the queried date range
- Check that the events are in the calendar you shared (not a different calendar)
- Ensure the shareable link is still active

### Tests failing
If tests fail:
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check Python version: `python --version` (should be 3.8+)
3. Run tests with verbose output: `pytest tests/ -v -s`

## Development

To test the server manually:

```bash
python server.py
```

The server will start and wait for MCP protocol messages on stdin.

### Project Structure

```
proton-calendar-mcp/
├── server.py                   # Main MCP server implementation
├── daily_summary.py            # Daily summary agent with intelligent prep suggestions
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── README.md                   # This file
└── tests/
    ├── test_calendar_fetch.py  # MCP server test suite
    └── test_daily_summary.py   # Daily summary agent test suite
```

## Limitations

- **Read-only**: This server can only read calendar data, not create or modify events
- **No CalDAV**: Proton Calendar doesn't support CalDAV, so we use shareable URLs
- **No API**: Proton doesn't provide a public API, so this relies on .ics export
- **Single calendar**: Each server instance can only access one shared calendar

## Future Enhancements

Potential improvements:
- Support for multiple calendars
- Caching to reduce API calls
- Event search by keywords
- Support for recurring events
- Export events to different formats

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Credits

Built with:
- [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic
- [icalendar](https://github.com/collective/icalendar) library
- [httpx](https://github.com/encode/httpx) async HTTP client
