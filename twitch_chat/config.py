# Filename: BASE/tools/installed/twitch_chat/config.py
"""
Twitch Chat Tool Configuration
All settings for Twitch IRC chat monitoring and messaging
"""

# =============================================================================
# TOOL CONTROL
# =============================================================================

# Enable/disable this tool
# Set to True to activate Twitch chat
ENABLED = False

# =============================================================================
# TWITCH CHAT SETTINGS
# =============================================================================

# Twitch channel to monitor (without the # symbol)
# Example: "shroud" for twitch.tv/shroud
TWITCH_CHANNEL = "ironmouse"

# OAuth token for authenticated mode (required to send messages)
# Get your token from: https://twitchapps.com/tmi/
# Format: "oauth:your_token_here"
# Leave empty for read-only mode
TWITCH_OAUTH_TOKEN = ""

# Bot nickname (required if using OAuth token)
# This should be your Twitch username
TWITCH_NICKNAME = ""

# Maximum number of messages to keep in context buffer
TWITCH_MAX_CONTEXT = 10

# Auto-start monitoring when tool is enabled
TWITCH_AUTO_START = True

# =============================================================================
# BATCH PROCESSING SETTINGS (NEW)
# =============================================================================

# Enable batch processing (sends messages to thought buffer in chunks)
# When enabled, incoming messages are collected and sent every TWITCH_BATCH_INTERVAL seconds
TWITCH_ENABLE_BATCHING = True

# Batch interval in seconds (how often to send accumulated messages to thought buffer)
# Default: 5.0 seconds
# Lower values = more frequent updates but more processing overhead
# Higher values = less overhead but less responsive to chat
TWITCH_BATCH_INTERVAL = 5.0

# =============================================================================
# ADVANCED SETTINGS
# =============================================================================

# IRC server settings (usually don't need to change)
TWITCH_IRC_SERVER = "irc.chat.twitch.tv"
TWITCH_IRC_PORT = 6667

# Connection settings
TWITCH_CONNECTION_TIMEOUT = 10.0
TWITCH_RECONNECT_DELAY = 5.0

# Rate limiting (Twitch limits message sending)
TWITCH_MESSAGE_RATE_LIMIT = 1  # Messages per 30 seconds (normal users)
# Verified bots can send 100 messages per 30 seconds

# Message parsing settings
TWITCH_PARSE_EMOTES = True
TWITCH_PARSE_BADGES = True

# =============================================================================
# USAGE INSTRUCTIONS
# =============================================================================
"""
READ-ONLY MODE (Monitor only):
1. Set TWITCH_CHANNEL to the channel name (e.g., "shroud")
2. Leave TWITCH_OAUTH_TOKEN and TWITCH_NICKNAME empty
3. Set ENABLED = True
4. Batch processing will automatically collect and send messages to thought buffer

AUTHENTICATED MODE (Monitor + Send messages):
1. Get OAuth token from https://twitchapps.com/tmi/
2. Set TWITCH_CHANNEL to your channel name
3. Set TWITCH_OAUTH_TOKEN to "oauth:your_token_here"
4. Set TWITCH_NICKNAME to your Twitch username
5. Set ENABLED = True

BATCH PROCESSING:
- When TWITCH_ENABLE_BATCHING = True, messages are collected and sent to the
  agent's thought buffer every TWITCH_BATCH_INTERVAL seconds
- This reduces processing overhead while keeping the agent informed of chat activity
- The agent will see batches formatted as:
  
  ## TWITCH CHAT (#channel)
  3 new messages:
  
  user1: Hello!
  user2: How's the stream?
  user3: Nice gameplay!

- Messages mentioning the bot will be flagged with [MENTIONED YOU]
- Adjust TWITCH_BATCH_INTERVAL based on chat activity:
  * Fast chat (100+ msg/min): 3-5 seconds
  * Medium chat (20-100 msg/min): 5-10 seconds  
  * Slow chat (<20 msg/min): 10-15 seconds

NOTES:
- Read-only mode uses anonymous connection (justinfan)
- Authenticated mode required to send messages
- Uses IRC protocol (irc.chat.twitch.tv:6667)
- Auto-reconnects on disconnect
- Batch processing runs in separate thread
- Thread-safe buffer operations

COMMANDS:
- twitch_chat.start - Start monitoring
- twitch_chat.stop - Stop monitoring
- twitch_chat.send_message - Send message (requires OAuth)
- twitch_chat.get_context - Get recent messages
"""