# Discord Integration - GUI Setup Guide

Complete guide for setting up and using Discord integration with your local Ollama-based VTuber AI through the graphical interface.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Discord Bot Creation](#discord-bot-creation)
3. [GUI Configuration](#gui-configuration)
4. [Testing & Verification](#testing--verification)
5. [Usage & Features](#usage--features)
6. [Advanced Configuration](#advanced-configuration)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Prerequisites

### Required Software

```bash
# Python 3.11+ with virtual environment
python --version  # Should be 3.11.9 or higher

# Ollama running locally
ollama --version
ollama list  # Verify models are installed

# Required Python packages
pip install discord.py  # Discord integration
pip install requests    # For API calls
```

### Required Ollama Models

```bash
# Text generation model
ollama pull llama3.2:3b-instruct-q4_K_M

# Vision model (optional, for image analysis)
ollama pull llava:7b-v1.5-q4_K_M

# Embedding model (for memory system)
ollama pull nomic-embed-text
```

### Verify Installation

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Verify Python packages
pip show discord.py
```

---

## Discord Bot Creation

### Step 1: Create Discord Application

1. **Navigate to Discord Developer Portal**
   - Go to: https://discord.com/developers/applications
   - Log in with your Discord account

2. **Create New Application**
   - Click **"New Application"**
   - Enter a name (e.g., "Anna AI Bot")
   - Click **"Create"**

3. **Configure Application**
   - Add an **App Icon** (optional)
   - Add a **Description** (optional)
   - Save changes

### Step 2: Create Bot User

1. **Go to Bot Section**
   - Click **"Bot"** in left sidebar
   - Click **"Add Bot"**
   - Confirm by clicking **"Yes, do it!"**

2. **Configure Bot Settings**
   - **Username**: Set your bot's display name
   - **Icon**: Upload bot avatar (optional)
   - **Public Bot**: Toggle OFF (recommended for personal use)
   - **Require OAuth2 Code Grant**: Leave OFF

3. **Copy Bot Token** ⚠️ IMPORTANT
   - Click **"Reset Token"** (if needed)
   - Click **"Copy"** to copy your bot token
   - **Save this token securely** - you'll need it for the GUI
   - ⚠️ Never share this token publicly!

### Step 3: Enable Required Intents

**Critical: Discord bots need special permissions to read messages**

1. Scroll down to **"Privileged Gateway Intents"**
2. Enable the following intents:
   - ✅ **Presence Intent** (optional, for user status)
   - ✅ **Server Members Intent** (recommended)
   - ✅ **Message Content Intent** (REQUIRED - bot can't read messages without this!)

3. Click **"Save Changes"**

> 🔴 **CRITICAL**: Without Message Content Intent, your bot will see messages but can't read their content!

### Step 4: Generate Invite Link

1. **Go to OAuth2 > URL Generator**
   - Click **"OAuth2"** in left sidebar
   - Click **"URL Generator"**

2. **Select Scopes**
   - ✅ `bot`
   - ✅ `applications.commands`

3. **Select Bot Permissions**

   **Text Permissions:**
   - ✅ Read Messages/View Channels
   - ✅ Send Messages
   - ✅ Send Messages in Threads
   - ✅ Create Public Threads
   - ✅ Create Private Threads
   - ✅ Embed Links
   - ✅ Attach Files
   - ✅ Read Message History
   - ✅ Add Reactions
   - ✅ Use Slash Commands

   **Optional Permissions:**
   - ✅ Manage Messages (for cleanup)
   - ✅ Manage Threads (for thread management)

4. **Copy Generated URL**
   - Scroll to bottom
   - Copy the generated URL

### Step 5: Invite Bot to Server

1. **Open Invite URL**
   - Paste the URL in your browser
   - Select your server from dropdown
   - Click **"Continue"**

2. **Authorize Permissions**
   - Review permissions
   - Click **"Authorize"**
   - Complete CAPTCHA if prompted

3. **Verify Bot Joined**
   - Open Discord
   - Check your server's member list
   - Bot should appear offline (will show online when started)

---

## GUI Configuration

### Step 1: Launch the GUI

```bash
# Navigate to project directory
cd C:\Users\YourUsername\Desktop\Anna_AI

# Activate virtual environment (if using)
venv\Scripts\activate

# Launch GUI
python BASE/interface/gui_interface.py
```

Or use the launcher script:
```bash
python run_gui.py
```

### Step 2: Navigate to Discord Panel

1. **Open GUI**
2. **Click "Controls" tab** (top of window)
3. **Scroll down** in right panel to find **"Discord Bot"** section

### Step 3: Configure Discord Settings

#### Basic Configuration

1. **Bot Token** (Required)
   - Paste your bot token from Discord Developer Portal
   - Click **"Show"** button to verify token (optional)
   - ⚠️ Keep this secure - don't screenshot with token visible!

2. **Command Prefix** (Default: `!`)
   - Set the prefix for bot commands
   - Examples: `!`, `?`, `>>`, `.`
   - Bot will respond to: `!ping`, `!status`, etc.

3. **Auto-start on Launch**
   - ✅ Check to start bot automatically when GUI launches
   - ❌ Uncheck to start manually with "Start Bot" button

#### Channel & Server Restrictions (Optional)

4. **Allowed Channels** (Leave empty for all channels)
   - Enter channel IDs separated by commas
   - Example: `123456789012345678,987654321098765432`
   - Bot will ONLY respond in these channels
   - **How to get Channel ID:**
     1. Enable Developer Mode: Settings > Advanced > Developer Mode
     2. Right-click any channel
     3. Click "Copy ID"

5. **Allowed Guilds** (Leave empty for all servers)
   - Enter server/guild IDs separated by commas
   - Example: `111111111111111111,222222222222222222`
   - Bot will ONLY operate in these servers
   - **How to get Server ID:**
     1. Right-click server icon
     2. Click "Copy ID"

#### Response Behavior

6. **Respond to Mentions**
   - ✅ Bot responds when @mentioned: `@BotName hello!`
   - ❌ Bot ignores mentions

7. **Respond to Replies**
   - ✅ Bot responds when you reply to its messages
   - ❌ Bot ignores replies

8. **Respond to DMs**
   - ✅ Bot responds to direct messages
   - ❌ Bot ignores DMs

### Step 4: Save Configuration

1. **Click "Save Settings"** button
   - Settings are saved to `personality/config.json`
   - Confirmation message appears
   - Settings persist between sessions

2. **Verify Settings Saved**
   - Check system log (bottom of GUI)
   - Should see: "✓ Discord settings saved to config.json"

---

## Testing & Verification

### Test 1: Connection Test

1. **Click "Test Connection"** button
2. **Expected Results:**
   - System log shows: "Testing Discord connection..."
   - System log shows: "✓ Connected as YourBotName"
   - System log shows: "✓ Bot ID: 123456789"
   - Popup: "Connection test successful!"

**If Test Fails:**
- ❌ "Invalid bot token" → Token is wrong, get new token from Discord
- ❌ "Connection test failed" → Check internet connection
- ❌ "discord.py not installed" → Run `pip install discord.py`

### Test 2: Start the Bot

1. **Click "Start Bot"** button
2. **Monitor Status Label:**
   - Changes from "Not Initialized" → "Starting..." → "Connected & Running"
   - Color changes to green when connected

3. **Check Discord:**
   - Bot's status changes from offline to online
   - Bot appears in member list with green dot

4. **Verify Statistics:**
   - Messages Received: 0
   - Messages Sent: 0
   - Errors: 0
   - Servers: 1 (or number of servers bot is in)
   - Uptime: 0.0h
   - Prefix: ! (or your custom prefix)

### Test 3: Send Test Message

1. **Go to Discord**
2. **In an allowed channel, send:**
   ```
   @YourBotName hello!
   ```

3. **Expected Behavior:**
   - Bot shows typing indicator (...)
   - Bot responds with AI-generated message
   - GUI system log shows: "Discord message processing..."

4. **Check GUI Statistics:**
   - Messages Received: 1
   - Messages Sent: 1

### Test 4: Try Bot Commands

```
!ping          → Bot responds with latency
!status        → Bot shows statistics
!help          → Shows available commands
```

---

## Usage & Features

### How the Bot Responds

The bot will respond to messages in these scenarios:

#### 1. Mentions
```
@BotName what's the weather like?
@BotName can you help me with Python?
```

#### 2. Replies
```
[Reply to any bot message]
User: "Can you elaborate on that?"
```

#### 3. Direct Messages
```
[Send DM to bot]
User: "Hello, I need help"
```

#### 4. Commands
```
!ping          - Check bot responsiveness
!status        - View bot statistics
!clear_context - Clear conversation memory
```

### Conversation Context

The bot maintains conversation context:

```
User: @BotName what's 5 + 5?
Bot: 5 + 5 equals 10.

User: @BotName what about multiplying that by 2?
Bot: 10 multiplied by 2 equals 20.
```

The bot remembers the previous exchange!

### Message History

- Bot keeps last **10 messages** as context (configurable in `config.json`)
- Provides relevant responses based on conversation flow
- Context automatically cleared when conversation is inactive

### Long Messages

Bot automatically splits long responses:

```
Bot: [Message part 1/3]
This is a very long response that exceeds Discord's 2000 
character limit, so it's automatically split into multiple 
messages...

Bot: [Message part 2/3]
...continuing from the previous message...

Bot: [Message part 3/3]
...and here's the conclusion.
```

### Multiple Users

Bot can handle multiple conversations simultaneously:

```
User1: @BotName tell me a joke
[Bot responds to User1]

User2: @BotName what's the capital of France?
[Bot responds to User2]

User1: @BotName that was funny!
[Bot continues User1's conversation]
```

---

## Advanced Configuration

### Editing config.json Directly

For advanced users, edit `personality/config.json`:

```json
{
  "discord": {
    "enabled": true,
    "bot_token": "YOUR_TOKEN_HERE",
    "command_prefix": "!",
    "auto_start": true,
    "allowed_channels": [123456789, 987654321],
    "allowed_guilds": [],
    "respond_to_mentions": true,
    "respond_to_replies": true,
    "respond_to_dms": true,
    "respond_in_threads": true,
    "typing_indicator": true,
    "message_history_limit": 10,
    "max_message_length": 2000,
    "split_long_messages": true,
    "command_cooldown": 3
  }
}
```

### Advanced Settings Explained

| Setting | Default | Description |
|---------|---------|-------------|
| `respond_in_threads` | `true` | Respond in thread conversations |
| `typing_indicator` | `true` | Show "typing..." while generating |
| `message_history_limit` | `10` | Number of messages to keep as context |
| `max_message_length` | `2000` | Discord's message character limit |
| `split_long_messages` | `true` | Auto-split messages over limit |
| `command_cooldown` | `3` | Seconds between command uses |

### Controls.py Settings

Edit `personality/controls.py` for Discord-specific behavior:

```python
# Discord specific settings
IN_DISCORD_CHAT = True              # Enable Discord integration
INCLUDE_DISCORD_CONTEXT = True      # Include Discord message context

DISCORD_RESPOND_TO_MENTIONS = True  # Respond to @mentions
DISCORD_RESPOND_TO_REPLIES = True   # Respond to message replies
DISCORD_RESPOND_TO_DMS = True       # Respond to DMs
DISCORD_RESPOND_IN_THREADS = True   # Respond in threads
DISCORD_TYPING_INDICATOR = True     # Show typing indicator
DISCORD_MESSAGE_HISTORY_LIMIT = 10  # Context window size
DISCORD_MAX_MESSAGE_LENGTH = 2000   # Max message length
DISCORD_SPLIT_LONG_MESSAGES = True  # Auto-split long messages
DISCORD_LOG_MESSAGES = True         # Log messages for debugging
```

### Performance Tuning

#### For Faster Responses:
```json
{
  "ollama": {
    "temperature": 0.7,
    "max_tokens": 500,
    "num_ctx": 2048
  }
}
```

#### For Better Quality:
```json
{
  "ollama": {
    "temperature": 0.85,
    "max_tokens": 2000,
    "num_ctx": 4096
  }
}
```

#### For Multiple Concurrent Users:
```bash
# Set environment variable before starting Ollama
set OLLAMA_NUM_PARALLEL=4
ollama serve
```

---

## Troubleshooting

### Bot Not Responding

**Problem**: Bot is online but doesn't respond to messages

**Solutions:**

1. **Check Message Content Intent**
   ```
   Discord Developer Portal > Bot > Privileged Gateway Intents
   ✅ Message Content Intent must be enabled!
   ```

2. **Verify Channel Restrictions**
   - If `allowed_channels` is set, bot only responds in those channels
   - Try in a different channel or clear restrictions

3. **Check Response Settings**
   - Ensure "Respond to Mentions" is checked
   - Try mentioning bot: `@BotName hello`

4. **Review System Log**
   - Look for error messages in GUI
   - Common errors:
     - "discord.py not installed"
     - "Invalid token"
     - "Permission denied"

### Connection Issues

**Problem**: "Connection test failed" or bot won't start

**Solutions:**

1. **Verify Token**
   ```
   - Token should be 50+ characters
   - No spaces before/after
   - From Bot section, not OAuth2
   ```

2. **Check Firewall**
   ```
   Discord uses port 443 (HTTPS)
   Ensure your firewall allows outbound HTTPS
   ```

3. **Verify discord.py Installation**
   ```bash
   pip uninstall discord.py
   pip install discord.py
   ```

4. **Check Ollama Status**
   ```bash
   curl http://localhost:11434/api/tags
   ```

### Bot Responds Slowly

**Problem**: Bot takes 10+ seconds to respond

**Solutions:**

1. **Check Ollama Performance**
   ```bash
   # Monitor Ollama
   ollama ps
   
   # Check system resources
   Task Manager > Performance
   ```

2. **Reduce Context Size**
   ```json
   "discord": {
     "message_history_limit": 5,  // Reduce from 10
     "max_message_length": 1000   // Reduce from 2000
   }
   ```

3. **Use Smaller Model**
   ```json
   "models": {
     "text_model": "llama3.2:1b-instruct-q4_K_M"  // Faster, less accurate
   }
   ```

4. **Reduce Temperature**
   ```json
   "ollama": {
     "temperature": 0.7,  // Reduce from 0.85
     "max_tokens": 500    // Reduce from 1000
   }
   ```

### Multiple Bots or Rate Limiting

**Problem**: "Rate limited" or "Too many requests"

**Solutions:**

1. **Increase Cooldown**
   ```json
   "discord": {
     "command_cooldown": 5  // Increase from 3
   }
   ```

2. **Limit Responses**
   ```json
   "discord": {
     "respond_to_mentions": true,
     "respond_to_replies": false,  // Disable to reduce load
     "respond_to_dms": false        // Disable to reduce load
   }
   ```

3. **Use Channel Restrictions**
   ```json
   "discord": {
     "allowed_channels": [123456789]  // Limit to specific channels
   }
   ```

### Token Invalid After Working

**Problem**: Bot worked before, now shows "Invalid token"

**Solutions:**

1. **Token Was Regenerated**
   - If you clicked "Reset Token" in Discord portal
   - Get new token and update in GUI
   - Save settings

2. **Token Exposed**
   - Discord automatically invalidates exposed tokens
   - Generate new token
   - Be careful not to share/commit it

3. **Bot Deleted**
   - Check if bot still exists in Developer Portal
   - Recreate bot if necessary

---

## Best Practices

### Security

1. **Never Share Token**
   - Don't screenshot with token visible
   - Don't commit config.json to git
   - Don't share logs with token

2. **Use .gitignore**
   ```
   personality/config.json
   .env
   *.log
   ```

3. **Rotate Token Regularly**
   - Generate new token every few months
   - Update in GUI and save

4. **Restrict Permissions**
   - Only give bot necessary permissions
   - Use channel restrictions for sensitive servers

### Performance

1. **Monitor Resource Usage**
   - Watch GPU/CPU usage
   - Use smaller models if struggling
   - Close other GPU-intensive applications

2. **Optimize Context**
   - Keep `message_history_limit` reasonable (5-10)
   - Clear context regularly with `!clear_context`

3. **Use Parallel Processing**
   ```bash
   set OLLAMA_NUM_PARALLEL=4
   ```

### User Experience

1. **Set Clear Expectations**
   - Pin message explaining bot capabilities
   - Explain how to trigger responses (@mention, reply)

2. **Use Descriptive Status**
   - Set bot status to "Playing: Type @BotName to chat"
   - Add custom status for maintenance

3. **Moderate Content**
   - Enable content filter in controls.py
   - Monitor bot responses
   - Adjust personality in SYS_MSG.py

### Maintenance

1. **Regular Updates**
   ```bash
   pip install --upgrade discord.py
   ollama pull llama3.2:3b-instruct-q4_K_M
   ```

2. **Backup Configuration**
   ```bash
   copy personality\config.json personality\config.json.backup
   ```

3. **Monitor Logs**
   - Check system log regularly
   - Look for errors or warnings
   - Address issues promptly

4. **Test After Changes**
   - Use "Test Connection" before starting
   - Send test message after configuration changes
   - Monitor statistics for anomalies

---

## Quick Reference

### GUI Buttons

| Button | Action |
|--------|--------|
| Save Settings | Write config to config.json |
| Reload Config | Load config from config.json |
| Test Connection | Verify bot token validity |
| Start Bot | Start Discord bot |
| Stop Bot | Stop Discord bot |
| Refresh Status | Update statistics display |

### Discord Commands

| Command | Description |
|---------|-------------|
| `!ping` | Check bot responsiveness |
| `!status` | View bot statistics |
| `!clear_context` | Clear conversation context |
| `!help` | Show available commands |

### Key Shortcuts

| Action | Shortcut |
|--------|----------|
| Toggle token visibility | Click "Show" button |
| Quick restart | Stop Bot → Start Bot |
| Emergency stop | Close GUI |

---

## Support & Resources

### Documentation

- **Discord.py Docs**: https://discordpy.readthedocs.io/
- **Discord Developer Portal**: https://discord.com/developers/applications
- **Ollama Docs**: https://ollama.ai/docs

### Getting Help

1. **Check System Log** (GUI bottom panel)
2. **Review This Guide** (troubleshooting section)
3. **Check Discord Developer Portal** (bot status)
4. **Verify Ollama Status**: `ollama ps`

### Common Links

- Discord Developer Portal: https://discord.com/developers/applications
- Enable Developer Mode: Discord Settings > Advanced > Developer Mode
- Get Channel ID: Right-click channel > Copy ID
- Get Server ID: Right-click server icon > Copy ID

---

## Appendix

### Example Configurations

#### Personal Bot (Single User)
```json
{
  "discord": {
    "enabled": true,
    "bot_token": "YOUR_TOKEN",
    "command_prefix": "!",
    "auto_start": true,
    "allowed_channels": [],
    "allowed_guilds": [],
    "respond_to_mentions": true,
    "respond_to_replies": true,
    "respond_to_dms": true
  }
}
```

#### Community Bot (Multiple Users)
```json
{
  "discord": {
    "enabled": true,
    "bot_token": "YOUR_TOKEN",
    "command_prefix": "!",
    "auto_start": true,
    "allowed_channels": [123456789],
    "allowed_guilds": [],
    "respond_to_mentions": true,
    "respond_to_replies": false,
    "respond_to_dms": false
  }
}
```

#### Testing Bot (Restricted)
```json
{
  "discord": {
    "enabled": true,
    "bot_token": "YOUR_TOKEN",
    "command_prefix": ">>",
    "auto_start": false,
    "allowed_channels": [123456789],
    "allowed_guilds": [987654321],
    "respond_to_mentions": true,
    "respond_to_replies": true,
    "respond_to_dms": true
  }
}
```

---

**Last Updated**: 2025-10-23  
**Version**: 1.0  
**Compatible With**: Anna AI v2.0+, Discord.py 2.0+