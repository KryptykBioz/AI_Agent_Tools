# Filename: BASE/tools/installed/group_chat/config.py
"""
Group Chat Tool Configuration - DEFAULTS ONLY
Settings for agent-to-agent communication on same device

IMPORTANT: Agent-specific configuration should be in personality/bot_info.py
This file contains only default values for the BASE/ shared directory
"""

# Enable/disable this tool
ENABLED = False

# Network settings - DEFAULTS
# Override these in personality/bot_info.py:
#   group_chat_port = 54321  # Unique per agent
GROUP_CHAT_HOST = "127.0.0.1"
GROUP_CHAT_PORT = 54321  # Default fallback only

# Auto-start when tool is enabled
GROUP_CHAT_AUTO_START = True

# Message settings
GROUP_CHAT_MAX_MESSAGE_LENGTH = 5000
GROUP_CHAT_MESSAGE_QUEUE_SIZE = 100

# Connection settings
GROUP_CHAT_PEER_DISCOVERY_RANGE = 5
GROUP_CHAT_CONNECTION_TIMEOUT = 0.5
GROUP_CHAT_RECONNECT_INTERVAL = 10.0

# Logging
GROUP_CHAT_LOG_BROADCASTS = True
GROUP_CHAT_LOG_RECEIVES = True

# =============================================================================
# USAGE INSTRUCTIONS
# =============================================================================
"""
SETUP FOR MULTIPLE AGENTS:

1. AGENT-SPECIFIC CONFIGURATION (personality/bot_info.py):
   Each agent must define their unique port in personality/bot_info.py:
   
   Agent 1 - personality/bot_info.py:
   agentname = "Anna"
   group_chat_port = 54321
   
   Agent 2 - personality/bot_info.py:
   agentname = "Bob"
   group_chat_port = 54322
   
   Agent 3 - personality/bot_info.py:
   agentname = "Charlie"
   group_chat_port = 54323

2. ENABLE TOOL (personality/controls.py):
   Add to each agent's controls.py:
   IN_GROUP_CHAT = True

3. BASE/ DIRECTORY:
   The BASE/ directory remains unchanged and can be copied between agents.
   No modifications needed in BASE/tools/installed/group_chat/config.py

4. HOW IT WORKS:
   - When an agent generates a spoken response, it's automatically broadcast
   - Other agents receive it in their thought buffer with sender's name
   - Agents don't receive their own messages back
   - All communication happens locally (127.0.0.1)
   - Peer discovery checks ±5 ports from each agent's port

5. DIRECTORY STRUCTURE:
   Agent1/
   ├── BASE/ (shared core - unchanged between agents)
   │   └── tools/installed/group_chat/
   │       ├── config.py (defaults only, no changes needed)
   │       ├── tool.py
   │       └── information.json
   └── personality/
       ├── bot_info.py (agentname = "Anna", group_chat_port = 54321)
       └── controls.py (IN_GROUP_CHAT = True)
   
   Agent2/
   ├── BASE/ (same shared core)
   │   └── tools/installed/group_chat/
   │       └── config.py (same defaults)
   └── personality/
       ├── bot_info.py (agentname = "Bob", group_chat_port = 54322)
       └── controls.py (IN_GROUP_CHAT = True)

EXAMPLE SETUP:

# Agent 1 (Anna) - personality/bot_info.py
agentname = "Anna"
group_chat_port = 54321

# Agent 1 - personality/controls.py
IN_GROUP_CHAT = True


# Agent 2 (Bob) - personality/bot_info.py
agentname = "Bob"
group_chat_port = 54322

# Agent 2 - personality/controls.py
IN_GROUP_CHAT = True


# BASE/ directory is identical for both agents
# No changes needed in BASE/tools/installed/group_chat/config.py


Result: Anna and Bob hear each other's spoken responses in their thought buffers

NOTES:
- Only personality/ directory differs between agents
- BASE/ directory is completely generic and shared
- Port in bot_info.py overrides the default in this config
- If group_chat_port is not defined in bot_info.py, falls back to GROUP_CHAT_PORT (54321)
"""