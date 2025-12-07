# AI Agent Tools Documentation

This repository contains a comprehensive suite of tools that enable an AI agent to interact with various services, platforms, and systems. Each tool follows a standardized architecture with lifecycle management and consistent error handling.
Architecture Overview
All tools inherit from BaseTool and implement:

Lifecycle Management: initialize(), cleanup(), is_available()
Command Execution: execute(command, args) with standardized result format
Context Loops: Optional background monitoring for proactive awareness
Graceful Degradation: Tools return True on initialization even if unavailable

## Tools Catalog
### Search & Information Retrieval
Bing Search (bing_search)
Web search using Bing Search API for current information.
Commands:

search(query: str) - Search the web, returns top 5 results

Configuration:

bing_search_api_key - Bing API key (required)
bing_search_endpoint - API endpoint (optional)

Example:
json{"tool": "bing_search.search", "args": ["latest AI developments"]}

Wikipedia Search (wiki_search)
Wikipedia search with position tracking to ensure varied results on repeated queries.
Commands:

search(query: str, max_results: Optional[int]) - Search Wikipedia

Features:

Position tracking prevents repetitive content
Returns contextual chunks around query matches
Automatic cache reset when positions exhausted

Example:
json{"tool": "wiki_search.search", "args": ["quantum computing", 5]}

### Development & Coding
VS Code Integration (coding)
Integration with VS Code via Ollama Code Editor extension REST API.
Commands:

edit(instruction: str, file: Optional[str], selection: Optional[dict]) - Send coding instruction
fetch(file_path: str, start_line: Optional[int], end_line: Optional[int]) - Retrieve file content
verify(file_path: str, expected_changes: Optional[str]) - Verify changes
files() - List open files
status() - Check connection

Configuration:

vscode_server_url - Server URL (default: http://localhost:3000)
vscode_timeout - Request timeout (default: 30s)

Example:
json{"tool": "coding.edit", "args": ["add error handling to the login function"]}

### Gaming Integration
Minecraft Bot (minecraft)
Full bot control with command execution and proactive game state monitoring.
Commands:

gather_resource(resource: str, count: Optional[int])
goto_location(x: float, y: float, z: float)
move_direction(direction: str, distance: float)
attack_entity(entity: str)
craft_item(item: str, count: Optional[int])
use_item(item: str)
chat(message: str)
build(structure: str, size: Optional[int])

Context Loop:

Monitors game state every 5 seconds
Injects environmental data into thought buffer
Urgency calculated based on health, food, hostile mobs

Configuration:

MINECRAFT_API_HOST - Bot API host
MINECRAFT_API_PORT - Bot API port (default: 3001)


League of Legends Spectator (league_of_legends)
Real-time match monitoring and threat detection (spectator mode only).
Features:

Monitors Live Client API every 2 seconds
Detects critical events (kills, objectives, low HP)
Calculates threat levels automatically
No command execution (spectator only)

Context Loop:

Injects game state on critical events
Urgency levels from 1-10 based on threats
Champion stats, team scores, recent events

Configuration:

LEAGUE_API_HOST - Live Client API host
LEAGUE_API_PORT - API port (default: 2999)


### Chat Platform Integration
Discord Chat (discord_chat)
Discord bot with message monitoring and sending capabilities.
Commands:

start() - Start Discord bot
stop() - Stop Discord bot
send_message(message: str, channel_id: Optional[int])
get_context() - Get conversation history

Features:

Automatic message splitting for long content
Built-in commands: !ping, !status, !clear_context
Channel/guild restrictions support
Message callback system

Configuration:

DISCORD_BOT_TOKEN - Bot token (required)
DISCORD_COMMAND_PREFIX - Command prefix (default: !)
DISCORD_ALLOWED_CHANNELS - Channel whitelist
DISCORD_AUTO_START - Auto-start on initialize


Twitch Chat (twitch_chat)
Twitch IRC chat monitoring with batch processing and thought buffer injection.
Commands:

start() - Start monitoring
stop() - Stop monitoring
send_message(message: str) - Send message (requires OAuth)
get_context() - Get conversation history

Features:

FIXED: Proper initialization order ensures thought buffer capture
Batch processing every 5 seconds (configurable)
Direct mention detection
Read-only mode without OAuth

Configuration:

TWITCH_CHANNEL - Channel name (required)
TWITCH_OAUTH_TOKEN - OAuth token for sending
TWITCH_NICKNAME - Bot nickname
TWITCH_ENABLE_BATCHING - Enable batch processing (default: True)
TWITCH_BATCH_INTERVAL - Batch interval in seconds (default: 5.0)


YouTube Chat (youtube_chat)
YouTube live chat monitoring via internal API (monitor-only).
Commands:

start() - Start monitoring
stop() - Stop monitoring
get_context() - Get conversation history
send_message() - Not supported (YouTube API restriction)

Features:

Uses continuation tokens for real-time updates
No API key required
Automatic polling interval adjustment
Monitor-only mode (cannot send messages)

Configuration:

YOUTUBE_VIDEO_ID - Video ID to monitor
YOUTUBE_MAX_CONTEXT - Context buffer size (default: 10)
YOUTUBE_AUTO_START - Auto-start monitoring


### Animation & Avatar Control
Unity Animation (unity)
WebSocket-based VRM character animation control.
Commands:

emotion(emotion_name: str, intensity: Optional[float]) - Set emotion
animation(animation_name: str, intensity: Optional[float]) - Play animation
connect() - Connect to Unity
health() - Health check

Default Emotions:
happy, sad, angry, surprised, neutral, relaxed, excited, confused
Default Animations:
wave, nod, shake_head, bow, dance, jump, sit, stand, idle
Configuration:

unity_websocket_url - WebSocket URL (default: ws://127.0.0.1:19192)
unity_connection_timeout - Connection timeout (default: 5.0s)


Warudo Animation (warudo)
WebSocket-based Warudo avatar animation control.
Commands:

emotion(emotion_name: str) - Set emotion/expression
animation(animation_name: str) - Play animation

Configuration:

warudo_websocket_url - WebSocket URL (default: ws://127.0.0.1:19190)


### Vision & Multimedia
Screenshot Vision (vision)
Screen capture and AI-powered analysis using vision models.
Commands:

screenshot() - Capture and analyze primary monitor
analyze(query: str, monitor: Optional[int]) - Analyze with specific question

Features:

Multi-monitor support
Integration with Ollama vision models
Automatic base64 encoding

Configuration:

vision_model - Vision model name (default: llava:latest)
ollama_endpoint - Ollama server URL

Dependencies:
bashpip install pyautogui screeninfo pillow

Sound Effects (sound)
Audio playback system for enhancing interactions.
Commands:

play(sound_name: str, volume: Optional[float]) - Play sound effect
list() - List available sounds
stop() - Stop all sounds

Features:

Volume control per sound
Global volume setting
Supports .mp3 format
Throttling for repeated sounds

Configuration:

sound_effects_dir - Sound directory path
SOUND_EFFECT_VOLUME - Global volume (0.0-1.0)

Dependencies:
bashpip install pygame

### Productivity
Reminders (reminders)
Time-based reminders with natural language parsing and proactive notifications.
Commands:

create(description: str, time_phrase: str) - Create reminder
list() - List all active reminders
delete(reminder_id: str) - Delete reminder

Context Loop:

Checks every 30 minutes
Immediate notification for overdue reminders
Escalating urgency (3 notifications max)
Previews upcoming reminders

Time Phrases:

"in 30 minutes", "in 2 hours"
"tomorrow at 3pm"
"next monday at 10am"

Example:
json{"tool": "reminders.create", "args": ["take break", "in 30 minutes"]}

Common Patterns
Result Format
All tools return standardized results:
#### Success
{
    "success": True,
    "content": "Human-readable result",
    "metadata": {"additional": "data"}
}

#### Error
{
    "success": False,
    "content": "Error description",
    "metadata": {"error_details": "..."},
    "guidance": "Suggested fix or alternative"
}
Context Loops
Tools with has_context_loop() -> True run background monitoring:

Purpose: Proactive awareness without explicit queries
Frequency: Tool-specific (2s to 30min intervals)
Injection: Adds data to thought buffer with urgency levels
Examples: Minecraft (5s), League (2s), Reminders (30min)

Graceful Degradation
Tools handle missing dependencies gracefully:
pythonasync def initialize(self) -> bool:
    if not DEPENDENCY_AVAILABLE:
        if self._logger:
            self._logger.warning("[Tool] Dependency missing")
        return True  # Still register tool
    
    # ... normal initialization
    return True
Error Handling
Consistent error reporting with guidance:
pythonreturn self._error_result(
    'Brief error description',
    metadata={'context': 'data'},
    guidance='Actionable suggestion for user'
)
Configuration
Tools read configuration from:

config.json - Main configuration file
controls.py - Runtime controls
Tool-specific config.py files

Common configuration patterns:
json{
    "bing_search_api_key": "your-key",
    "vscode_server_url": "http://localhost:3000",
    "unity_websocket_url": "ws://127.0.0.1:19192",
    "vision_model": "llava:latest",
    "sound_effects_dir": "/path/to/sounds"
}
Installation
Core Requirements
bashpip install requests asyncio
Optional Dependencies
bash# Discord
pip install discord.py

# Twitch/YouTube (built-in IRC/HTTP - no extra deps)

# Vision
pip install pyautogui screeninfo pillow

# Sound
pip install pygame

# Unity/Warudo
pip install websockets
Best Practices

Check Availability: Always verify is_available() before use
Handle Errors: Check result["success"] and provide feedback
Use Metadata: Extract additional context from result["metadata"]
Respect Guidance: Present result["guidance"] to users on errors
Monitor Context: Leverage context loops for proactive behavior
Cleanup: Tools automatically cleanup on shutdown

## Development
Creating a New Tool
pythonfrom BASE.handlers.base_tool import BaseTool

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"
    
    async def initialize(self) -> bool:
        # Setup
        return True
    
    async def cleanup(self):
        # Teardown
        pass
    
    def is_available(self) -> bool:
        return True
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        # Implementation
        return self._success_result("Done")
Adding Context Loop
pythondef has_context_loop(self) -> bool:
    return True

async def context_loop(self, thought_buffer):
    while self._running:
        # Monitor and inject
        thought_buffer.add_processed_thought(
            content="Context data",
            source="tool_name",
            urgency_override=5
        )
        await asyncio.sleep(interval)

Contributing
@KryptykBioz