# Proton Calendar MCP Server

An MCP (Model Context Protocol) server that provides read-only access to your Proton Calendar data and optionally integrates with Trello for task management, all accessible through AI assistants like Claude Code.

## Features

### Calendar Features
- **Read-only access** to your Proton Calendar via shareable URL
- **Three calendar tools** for querying events:
  - `get_today_events`: Get all events scheduled for today
  - `get_week_events`: Get all events for the next 7 days
  - `get_date_range_events`: Get events for a custom date range

### Trello Integration (Optional)
- **Read-only access** to your Trello boards and cards
- **Four Trello tools** for task management:
  - `get_trello_cards_today`: Get all cards due today
  - `get_trello_cards_tomorrow`: Get all cards due tomorrow
  - `get_trello_overdue_cards`: Get overdue cards with day count
  - `get_trello_cards_date_range`: Get cards due within a date range
- **Rich card details**: Labels, checklists, descriptions, board/list info
- **Automatic board filtering** via environment variable

### Other Features
- **Comprehensive tests** to ensure reliable data fetching
- **Daily summary agent** with intelligent preparation suggestions

## Prerequisites

- Python 3.8 or higher (tested with Python 3.13)
- A Proton Calendar account
- A shareable calendar URL from Proton Calendar (read-only)
- (Optional) A Trello account with API key and token for Trello integration

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

### 3. Set Environment Variables

#### Required: Proton Calendar URL

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

#### Optional: Trello Integration

To enable Trello integration, you need to set up Trello API credentials:

1. **Get your Trello API Key:**
   - Go to https://trello.com/power-ups/admin
   - Click "New" to create a new Power-Up
   - Your API key will be displayed

2. **Generate a Trello Token:**
   - Visit: `https://trello.com/1/authorize?expiration=never&name=ProtonCalendarMCP&scope=read&response_type=token&key=YOUR_API_KEY`
   - Replace `YOUR_API_KEY` with your actual API key
   - Click "Allow" to generate your token

3. **Set environment variables:**

**Windows (PowerShell):**
```powershell
$env:TRELLO_API_KEY="your_api_key_here"
$env:TRELLO_TOKEN="your_token_here"
$env:TRELLO_BOARD_IDS="board_id_1,board_id_2"  # Optional: comma-separated board IDs
```

**Linux/Mac:**
```bash
export TRELLO_API_KEY="your_api_key_here"
export TRELLO_TOKEN="your_token_here"
export TRELLO_BOARD_IDS="board_id_1,board_id_2"  # Optional: comma-separated board IDs
```

**Note:** If `TRELLO_BOARD_IDS` is not set, the server will fetch cards from all your boards.

### 4. Register with Claude Code

Register the MCP server with Claude Code using stdio transport:

**With Trello integration:**
```bash
claude mcp add --transport stdio proton-calendar \
  --env PROTON_CALENDAR_URL="YOUR_CALENDAR_URL" \
  --env TRELLO_API_KEY="YOUR_TRELLO_KEY" \
  --env TRELLO_TOKEN="YOUR_TRELLO_TOKEN" \
  --env TRELLO_BOARD_IDS="board_id_1,board_id_2" \
  -- python /path/to/server.py
```

**Without Trello (calendar only):**
```bash
claude mcp add --transport stdio proton-calendar \
  --env PROTON_CALENDAR_URL="YOUR_CALENDAR_URL" \
  -- python /path/to/server.py
```

**Important:**
- Replace `YOUR_CALENDAR_URL` with your actual Proton Calendar URL
- Replace Trello credentials with your actual API key and token
- Update the path to match where you saved `server.py`
- For Windows, use backslashes: `C:\path\to\server.py`
- `TRELLO_BOARD_IDS` is optional - omit to fetch from all boards

**Alternative:** Set environment variables system-wide, then register without the `--env` flags:

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

Once configured, you can ask Claude Code questions about both your calendar and Trello boards:

**Calendar queries:**
- "What's on my calendar today?"
- "Show me my schedule for the next week"
- "What events do I have between January 15 and January 20?"

**Trello queries (if configured):**
- "What Trello cards are due today?"
- "Show me my overdue Trello tasks"
- "What cards do I have due tomorrow?"
- "Show me Trello cards due this week"

**Combined queries:**
- "What do I have on my schedule today, including Trello tasks?"
- "Show me everything due tomorrow - calendar and Trello"

Claude Code will automatically use the appropriate tools to fetch and display your data.

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

### Calendar Tools

#### get_today_events
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

#### get_week_events
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

#### get_date_range_events
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

### Trello Tools

**Note:** Trello tools are only available if Trello credentials are configured.

#### get_trello_cards_today
Returns all Trello cards due today.

**No parameters required**

**Example output:**
```
Trello Cards Due Today:

• Fix authentication bug
  Board: Development → In Progress
  Due: 02:00 PM
  Labels: High Priority, Bug
  Checklist: 2/5 completed
  URL: https://trello.com/c/abc123

• Review pull request
  Board: Development → Review
  Due: 04:00 PM
  Labels: Review
  URL: https://trello.com/c/def456
```

#### get_trello_cards_tomorrow
Returns all Trello cards due tomorrow.

**No parameters required**

**Output format:** Same as `get_trello_cards_today`

#### get_trello_overdue_cards
Returns all overdue Trello cards with days overdue count.

**No parameters required**

**Example output:**
```
Overdue Trello Cards (3 total):

• Update documentation
  Board: Documentation → To Do
  Due: 2025-11-10 09:00 AM (3 days overdue)
  Labels: Documentation
  Checklist: 0/3 completed
  URL: https://trello.com/c/ghi789
```

#### get_trello_cards_date_range
Returns Trello cards due within a specified date range.

**Parameters:**
- `start_date` (string): Start date in YYYY-MM-DD format
- `end_date` (string): End date in YYYY-MM-DD format

**Example output:**
```
Trello Cards Due 2025-11-13 to 2025-11-20:

Wednesday, November 13, 2025:
  • Deploy to production
    Board: Operations → Scheduled
    Due: 02:00 PM
    Labels: Deploy, Critical
    Checklist: 5/7 completed
    URL: https://trello.com/c/jkl012

Thursday, November 14, 2025:
  • Team retrospective
    Board: Team → Meetings
    Due: 10:00 AM
    URL: https://trello.com/c/mno345
```

## Testing

Run the test suite to verify all functionality:

```bash
cd proton-calendar-mcp
pytest tests/ -v
```

All tests should pass:
```
37 passed in 2.5s
```

### Test Coverage

The test suite includes:

**Calendar Fetching Tests (11 tests):**
- ✅ Successful calendar fetching
- ✅ HTTP error handling
- ✅ Invalid data handling
- ✅ Timeout handling
- ✅ Event formatting
- ✅ Date range filtering
- ✅ Today's events filtering
- ✅ Event sorting
- ✅ All-day event handling

**Daily Summary Agent Tests (12 tests):**
- ✅ Preparation analysis for meetings
- ✅ Preparation analysis for presentations
- ✅ Preparation analysis for interviews
- ✅ Location-based preparation
- ✅ Training event preparation
- ✅ Time formatting
- ✅ Event summary formatting
- ✅ Long description handling
- ✅ Multiline description handling

**Trello Client Tests (14 tests):**
- ✅ Client initialization and credentials
- ✅ Card formatting with all attributes
- ✅ Checklist progress tracking
- ✅ Label and attachment handling
- ✅ Date filtering (today, tomorrow, overdue)
- ✅ Date range filtering
- ✅ Card sorting by due date
- ✅ Edge cases (no due date, timezone handling)

## Architecture

### Components

**MCP Server (server.py):**
1. **fetch_calendar()**: Async function to fetch and parse iCalendar data from URL
2. **format_event()**: Extracts relevant information from calendar events
3. **filter_events_by_date_range()**: Filters and sorts events by date
4. **Trello Integration**: Optional Trello client for task management
5. **MCP Server**: Exposes 3 calendar tools + 4 Trello tools (if configured) via MCP

**Trello Client (trello_client.py):**
1. **TrelloCardFetcher**: Main client class for Trello API interaction
2. **get_cards_from_boards()**: Fetches cards from specified boards
3. **filter_cards_by_due_date()**: Filters and sorts cards by due date
4. **get_cards_due_today/tomorrow()**: Convenience methods for common queries
5. **get_overdue_cards()**: Identifies and returns past-due cards
6. **_format_card()**: Extracts comprehensive card details (labels, checklists, etc.)

**Daily Summary Agent (daily_summary.py):**
1. **generate_daily_summary()**: Creates comprehensive daily overview
2. **analyze_preparation_needs()**: Intelligent preparation suggestions
3. **format_event_summary()**: User-friendly event formatting
4. **Smart tips**: Early morning alerts, back-to-back meeting warnings

### Dependencies

- `mcp>=1.0.0` - Official Model Context Protocol SDK
- `icalendar>=6.0.0` - RFC 5545 compliant iCalendar parser
- `httpx>=0.27.0` - Modern async HTTP client
- `py-trello>=0.19.0` - Trello API client library
- `pytest>=8.0.0` - Testing framework
- `pytest-asyncio>=0.23.0` - Async support for pytest

## Security & Privacy

- This server only has **read-only** access to your calendar and Trello boards
- Your calendar URL and Trello credentials should be kept private
- The MCP server runs locally on your machine
- No data is sent to third-party services except:
  - Proton's servers to fetch your calendar
  - Trello's API to fetch your cards (if configured)
- All credentials are passed via environment variables for security
- Trello integration is optional - works fine without it

## Troubleshooting

### Calendar Issues

**"PROTON_CALENDAR_URL environment variable is not set"**
- Make sure you've set the environment variable before running the server
- You can either set it system-wide or pass via `--env` flag when registering with Claude Code

**"Error fetching calendar: [HTTP error]"**
- Verify your calendar URL is correct
- Check that the URL is publicly accessible (test it in a browser)
- Ensure you have internet connectivity
- Make sure the calendar URL hasn't expired

**Events not showing up**
- Verify events exist in your Proton Calendar for the queried date range
- Check that the events are in the calendar you shared (not a different calendar)
- Ensure the shareable link is still active

### Trello Issues

**Trello tools not appearing**
- Verify `TRELLO_API_KEY` and `TRELLO_TOKEN` are set correctly
- Check that credentials are passed to the MCP server via `--env` flags or system environment
- Restart Claude Code after setting environment variables

**"Error: Trello is not configured"**
- This means the Trello credentials are missing or invalid
- Double-check your API key and token
- Ensure environment variables are set before the server starts

**No cards returned from Trello**
- Verify you have cards with due dates in your boards
- Check that `TRELLO_BOARD_IDS` (if set) contains valid board IDs
- Ensure your API token has read access to the boards

**How to find Trello Board IDs:**
1. Open your Trello board in a browser
2. Add `.json` to the end of the URL: `https://trello.com/b/BOARD_ID/board-name.json`
3. Look for the `id` field in the JSON response
4. Use this ID in the `TRELLO_BOARD_IDS` environment variable

### General Issues

**Tests failing**
If tests fail:
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check Python version: `python --version` (should be 3.8+)
3. Run tests with verbose output: `pytest tests/ -v -s`

**Server not responding**
- Check that the server process is running
- Verify Claude Code is properly connected: `claude mcp list`
- Look for error messages in the server logs

## Development

To test the server manually:

```bash
python server.py
```

The server will start and wait for MCP protocol messages on stdin.

### Project Structure

```
proton-calendar-mcp/
├── server.py                          # Main MCP server implementation
├── trello_client.py                   # Trello API client module
├── daily_summary.py                   # Daily summary agent with intelligent prep suggestions
├── requirements.txt                   # Python dependencies
├── pytest.ini                         # Pytest configuration
├── README.md                          # This file
└── tests/
    ├── test_calendar_fetch.py         # Calendar MCP server test suite
    ├── test_daily_summary.py          # Daily summary agent test suite
    ├── test_trello_client.py          # Trello client test suite
    └── test_server_trello_integration.py  # Trello MCP integration tests
```

## Limitations

### Calendar Limitations
- **Read-only**: This server can only read calendar data, not create or modify events
- **No CalDAV**: Proton Calendar doesn't support CalDAV, so we use shareable URLs
- **No API**: Proton doesn't provide a public API, so this relies on .ics export
- **Single calendar**: Each server instance can only access one shared calendar

### Trello Limitations
- **Read-only**: This server can only read Trello cards, not create or modify them
- **Due dates only**: Only cards with due dates are returned by the filtering functions
- **No webhooks**: The server polls Trello on each request (no real-time updates)
- **Rate limits**: Trello API has rate limits (300 requests per 10 seconds per token)

## Future Enhancements

Potential improvements:
- Support for multiple Proton calendars
- Caching to reduce API calls for both services
- Event/card search by keywords
- Support for recurring events
- Write capabilities for Trello (create/update cards)
- Trello card comments and activity
- Export data to different formats
- Integration with other task management systems

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Credits

Built with:
- [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic
- [icalendar](https://github.com/collective/icalendar) library
- [httpx](https://github.com/encode/httpx) async HTTP client
