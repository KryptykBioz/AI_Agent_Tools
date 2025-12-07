# Filename: BASE/tools/installed/youtube_chat/config.py
"""
YouTube Chat Tool Configuration
All settings for YouTube live stream monitoring
"""

# =============================================================================
# TOOL CONTROL
# =============================================================================

# Enable/disable this tool
# Set to True to activate YouTube chat monitoring
ENABLED = False

# =============================================================================
# YOUTUBE CHAT SETTINGS
# =============================================================================

# YouTube video ID for live stream monitoring
# Find this in the URL: youtube.com/watch?v=VIDEO_ID
# Example: "dQw4w9WgXcQ" for https://www.youtube.com/watch?v=dQw4w9WgXcQ
YOUTUBE_VIDEO_ID = ""

# Maximum number of messages to keep in context buffer
YOUTUBE_MAX_CONTEXT = 10

# Auto-start monitoring when tool is enabled
YOUTUBE_AUTO_START = False

# Connection timeout (seconds)
YOUTUBE_CONNECTION_TIMEOUT = 10

# Retry settings
YOUTUBE_MAX_RETRIES = 3
YOUTUBE_RETRY_DELAY = 2.0

# =============================================================================
# USAGE INSTRUCTIONS
# =============================================================================
"""
SETUP:
1. Find your live stream video ID from the URL
   Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ
   Video ID: dQw4w9WgXcQ

2. Set YOUTUBE_VIDEO_ID above to your video ID

3. Set ENABLED = True to activate the tool

4. Optionally set YOUTUBE_AUTO_START = True to start monitoring automatically

NOTES:
- YouTube chat is MONITOR-ONLY (cannot send messages via API)
- Stream must be live with chat enabled
- Uses continuation tokens to fetch messages
- Polls every 2-5 seconds based on YouTube's response
- No API key required (uses public API)

COMMANDS:
- youtube_chat.start - Start monitoring
- youtube_chat.stop - Stop monitoring
- youtube_chat.get_context - Get recent messages
"""