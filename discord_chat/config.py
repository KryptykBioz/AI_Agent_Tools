# Filename: BASE/tools/installed/discord_chat/config.py
"""
Discord Chat Tool Configuration
All settings for Discord bot integration
"""

# =============================================================================
# TOOL CONTROL
# =============================================================================

# Enable/disable this tool
# Set to True to activate Discord bot
ENABLED = False

# =============================================================================
# DISCORD BOT SETTINGS
# =============================================================================

# Discord bot token (REQUIRED)
# Get from: https://discord.com/developers/applications
# KEEP THIS SECRET! Never share or commit to git
DISCORD_BOT_TOKEN = ""

# Command prefix for bot commands
# Default: "!" (e.g., !ping, !status, !clear_context)
DISCORD_COMMAND_PREFIX = "!"

# Channel restrictions (list of channel IDs)
# If set, bot only responds in these channels
# Leave as None to allow all channels
# Example: [123456789012345678, 987654321098765432]
DISCORD_ALLOWED_CHANNELS = None

# Guild/Server restrictions (list of guild IDs)
# If set, bot only operates in these guilds
# Leave as None to allow all guilds
# Example: [123456789012345678]
DISCORD_ALLOWED_GUILDS = None

# Auto-start bot when tool is enabled
DISCORD_AUTO_START = False

# =============================================================================
# MESSAGE SETTINGS
# =============================================================================

# Maximum message length before splitting
# Discord limit is 2000, we use a buffer
DISCORD_MAX_MESSAGE_LENGTH = 2000

# Maximum number of messages to keep in context buffer
DISCORD_MAX_CONTEXT = 10

# Message splitting settings
DISCORD_SPLIT_ON_SENTENCES = True
DISCORD_SPLIT_DELAY = 0.5  # Seconds between split messages

# =============================================================================
# BOT PRESENCE
# =============================================================================

# Bot status
DISCORD_STATUS_TYPE = "online"  # online, idle, dnd, invisible

# Bot activity
DISCORD_ACTIVITY_TYPE = "playing"  # playing, watching, listening, streaming
DISCORD_ACTIVITY_NAME = "with AI"  # What the bot is doing

# =============================================================================
# BEHAVIOR SETTINGS
# =============================================================================

# Event handling
DISCORD_PROCESS_COMMANDS = True
DISCORD_PROCESS_MENTIONS = True
DISCORD_PROCESS_REPLIES = True

# Response settings
DISCORD_TYPING_INDICATOR = True  # Show typing indicator when processing
DISCORD_DELETE_COMMANDS = False  # Delete command messages after execution
DISCORD_EMBED_RESPONSES = False  # Use embeds for bot responses

# Mention settings
DISCORD_RESPOND_TO_MENTIONS = True
DISCORD_RESPOND_TO_REPLIES = True
DISCORD_ALLOW_EVERYONE_MENTION = False  # Allow @everyone in bot messages
DISCORD_ALLOW_ROLE_MENTIONS = False  # Allow @role in bot messages

# Logging verbosity
DISCORD_LOG_MESSAGES = True
DISCORD_LOG_COMMANDS = True
DISCORD_LOG_ERRORS = True

# =============================================================================
# RATE LIMITING
# =============================================================================

# Discord's rate limits
DISCORD_RATE_LIMIT_MESSAGES = 5  # Per 5 seconds per channel
DISCORD_RATE_LIMIT_DELAY = 0.5  # Delay between messages

# =============================================================================
# USAGE INSTRUCTIONS
# =============================================================================
"""
SETUP:

1. CREATE BOT:
   - Go to https://discord.com/developers/applications
   - Click "New Application"
   - Go to "Bot" section
   - Click "Add Bot"
   - Enable these Privileged Gateway Intents:
     * MESSAGE CONTENT INTENT (required!)
     * SERVER MEMBERS INTENT
     * PRESENCE INTENT

2. GET BOT TOKEN:
   - In Bot section, click "Reset Token"
   - Copy the token and set DISCORD_BOT_TOKEN above
   - KEEP THIS SECRET! Never share or commit to git

3. INVITE BOT TO SERVER:
   - Go to OAuth2 > URL Generator
   - Select scopes: "bot"
   - Select permissions:
     * Read Messages/View Channels
     * Send Messages
     * Read Message History
     * Add Reactions (optional)
     * Use External Emojis (optional)
   - Copy generated URL and open in browser
   - Select server and authorize

4. CONFIGURE (Optional):
   - Get channel/guild IDs (enable Developer Mode in Discord)
   - Set DISCORD_ALLOWED_CHANNELS to restrict to specific channels
   - Set DISCORD_ALLOWED_GUILDS to restrict to specific servers

5. ENABLE TOOL:
   - Set ENABLED = True above
   - Optionally set DISCORD_AUTO_START = True

NOTES:
- Bot requires "MESSAGE CONTENT INTENT" to read messages
- Without this intent, bot can only see @mentions
- Bot will ignore its own messages
- @everyone and @here mentions are automatically sanitized

COMMANDS:
- discord_chat.start - Start bot
- discord_chat.stop - Stop bot
- discord_chat.send_message - Send message to channel
- discord_chat.get_context - Get recent messages

BOT COMMANDS (in Discord):
- !ping - Check bot responsiveness
- !status - Show bot statistics
- !clear_context - Clear conversation context
"""