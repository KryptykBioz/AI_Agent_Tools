# Building a Communication Server: Ollama Agent ↔ Minecraft Bot

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Components](#architecture-components)
3. [Understanding Mineflayer](#understanding-mineflayer)
4. [Understanding Pathfinder](#understanding-pathfinder)
5. [Minecraft's Protocol & API](#minecrafts-protocol--api)
6. [Communication Flow](#communication-flow)
7. [Implementation Strategy](#implementation-strategy)
8. [Command Processing](#command-processing)
9. [Error Handling & Safety](#error-handling--safety)

---

## System Overview

This guide explains how to build a bridge between an **Ollama LLM agent** (running locally) and a **Minecraft bot** that can execute commands in-game. The system allows natural language instructions to be converted into actionable Minecraft commands.

### High-Level Flow
```
User Input → Ollama Agent → Communication Server → Minecraft Bot → Game Actions
                ↓                                         ↓
            NL Processing                          Command Execution
```

---

## Architecture Components

### 1. **Ollama Agent**
- Local LLM (e.g., Llama 2, Mistral, etc.)
- Processes natural language input
- Generates structured commands
- Runs on `http://localhost:11434` by default

### 2. **Communication Server**
- Middleware (typically Node.js/Express)
- Receives commands from Ollama
- Translates to Mineflayer API calls
- Manages bot state and responses

### 3. **Minecraft Bot (Mineflayer)**
- JavaScript library for creating Minecraft bots
- Connects to Minecraft servers
- Executes in-game actions
- Reports game state back to server

---

## Understanding Mineflayer

### What is Mineflayer?

Mineflayer is a high-level Node.js library that implements the Minecraft protocol, allowing you to create bots that can:
- Connect to Minecraft servers (Java Edition)
- Interact with the game world
- Perform player-like actions
- Read game state and events

### Core Capabilities

**Connection & Authentication:**
```javascript
const mineflayer = require('mineflayer');

const bot = mineflayer.createBot({
  host: 'localhost',
  port: 25565,
  username: 'AIBot',
  version: '1.20.1'  // Match server version
});
```

**Event System:**
- `bot.on('spawn', callback)` - Bot enters world
- `bot.on('chat', callback)` - Chat message received
- `bot.on('health', callback)` - Health/food changes
- `bot.on('death', callback)` - Bot dies

**Basic Actions:**
- **Chat:** `bot.chat(message)`
- **Look:** `bot.lookAt(position)`
- **Movement:** `bot.setControlState('forward', true)`
- **Inventory:** `bot.inventory.items()`
- **Block Interaction:** `bot.dig(block)`, `bot.placeBlock(block)`

### Key Mineflayer Objects

**`bot.entity`** - Bot's own entity data (position, health, etc.)
**`bot.entities`** - All entities in render distance
**`bot.players`** - Connected players
**`bot.blockAt(position)`** - Query blocks in the world

---

## Understanding Pathfinder

### What is Pathfinder?

Pathfinder (mineflayer-pathfinder) is a plugin for Mineflayer that adds intelligent navigation:
- A* pathfinding algorithm
- Obstacle avoidance
- Jump/swim/climb awareness
- Goal-based movement system

### Installation & Setup

```javascript
const { pathfinder, Movements, goals } = require('mineflayer-pathfinder');

bot.loadPlugin(pathfinder);
```

### Movement Configuration

**Movements Class:**
Defines what actions the bot can perform while pathfinding:
```javascript
const mcData = require('minecraft-data')(bot.version);
const defaultMove = new Movements(bot, mcData);

// Customize movement capabilities
defaultMove.canDig = true;        // Break blocks if needed
defaultMove.allow1by1towers = true; // Pillar up
defaultMove.scafoldingBlocks = []; // Blocks to use for bridging
```

### Goals System

Pathfinder uses **goals** to define destinations:

**GoalNear:** Get close to a position
```javascript
const { GoalNear } = goals;
const goal = new GoalNear(x, y, z, range);
```

**GoalBlock:** Stand on specific block
```javascript
const { GoalBlock } = goals;
const goal = new GoalBlock(x, y, z);
```

**GoalFollow:** Follow an entity
```javascript
const { GoalFollow } = goals;
const player = bot.players['username'].entity;
const goal = new GoalFollow(player, range);
```

**GoalXZ:** Reach X/Z coordinates (any Y)
```javascript
const { GoalXZ } = goals;
const goal = new GoalXZ(x, z);
```

### Executing Pathfinding

```javascript
bot.pathfinder.setMovements(defaultMove);
bot.pathfinder.setGoal(goal);

// Stop pathfinding
bot.pathfinder.setGoal(null);
```

### Pathfinding Events

- `path_update` - New path calculated
- `goal_reached` - Destination achieved
- `goal_updated` - Goal changed
- `path_stop` - Pathfinding cancelled

---

## Minecraft's Protocol & API

### Protocol Overview

Minecraft uses a **custom TCP-based protocol** with packet-based communication:

1. **Handshake** - Initial connection
2. **Login** - Authentication
3. **Play** - Game state packets

Mineflayer abstracts this complexity, but understanding helps with debugging.

### How Mineflayer Interfaces with Minecraft

**Packet Layer:**
- Mineflayer sends/receives raw packets
- Automatically handles protocol version differences
- Provides high-level API over low-level packets

**World Representation:**
- Chunks loaded as bot moves
- Blocks stored in local world model
- Entities tracked with position updates

**No Official API:**
Minecraft (Java Edition) doesn't have an official bot API. Mineflayer:
- Reverse-engineers the protocol
- Emulates a real client
- Must be updated for new Minecraft versions

### Limitations

- **Server-side restrictions:** Anti-cheat may kick bots
- **Rate limits:** Too many actions = connection issues
- **Version locking:** Bot version must match server
- **No modded server support** (without additional work)

---

## Communication Flow

### Step-by-Step Process

**1. User Input**
```
User: "Go to coordinates 100, 64, 200 and mine some coal"
```

**2. Ollama Processing**
The communication server sends this to Ollama with a system prompt:
```json
{
  "model": "llama2",
  "prompt": "Convert to JSON: Go to 100, 64, 200 and mine coal",
  "system": "You are a Minecraft command parser. Output JSON only."
}
```

**3. Ollama Response**
```json
{
  "actions": [
    {"type": "goto", "x": 100, "y": 64, "z": 200},
    {"type": "mine", "block": "coal_ore", "quantity": 1}
  ]
}
```

**4. Server Translation**
Communication server converts to Mineflayer calls:
```javascript
// Goto action
const goal = new goals.GoalBlock(100, 64, 200);
bot.pathfinder.setGoal(goal);

// Mine action (after arrival)
bot.once('goal_reached', async () => {
  const coalOre = bot.findBlock({
    matching: mcData.blocksByName.coal_ore.id,
    maxDistance: 32
  });
  if (coalOre) await bot.dig(coalOre);
});
```

**5. Bot Execution & Feedback**
```javascript
bot.on('goal_reached', () => {
  sendToOllama("Reached destination");
});

bot.on('diggingCompleted', (block) => {
  sendToOllama(`Mined ${block.name}`);
});
```

---

## Implementation Strategy

### Project Structure

```
project/
├── server.js           # Communication server
├── bot.js              # Mineflayer bot logic
├── ollama-client.js    # Ollama API wrapper
├── command-parser.js   # Command interpretation
└── actions/
    ├── movement.js     # Pathfinding actions
    ├── mining.js       # Block breaking
    ├── building.js     # Block placing
    └── combat.js       # Entity interaction
```

### Communication Server Setup

**Purpose:** Bridge between Ollama and Minecraft bot

**Key Responsibilities:**
- HTTP/WebSocket server for receiving commands
- Ollama API client for NL processing
- Bot command queue management
- State tracking and response routing

**Basic Structure:**
```javascript
const express = require('express');
const app = express();

// Endpoint for user input
app.post('/command', async (req, res) => {
  const userInput = req.body.text;
  
  // 1. Send to Ollama for parsing
  const parsed = await ollamaClient.parse(userInput);
  
  // 2. Queue commands for bot
  commandQueue.push(parsed.actions);
  
  // 3. Return acknowledgment
  res.json({ status: 'queued', actions: parsed.actions });
});

// Bot executes from queue
setInterval(() => {
  if (commandQueue.length > 0 && !bot.isBusy) {
    executeNextCommand(commandQueue.shift());
  }
}, 100);
```

### Ollama Integration

**API Communication:**
```javascript
async function queryOllama(prompt) {
  const response = await fetch('http://localhost:11434/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'llama2',
      prompt: prompt,
      stream: false,
      system: "You convert Minecraft commands to JSON. Output valid JSON only."
    })
  });
  
  return await response.json();
}
```

**Prompt Engineering:**
Critical for reliable command parsing:
- Provide examples of input/output pairs
- Specify exact JSON schema
- Include available commands list
- Add error handling instructions

---

## Command Processing

### Command Schema Design

**Standardized Format:**
```json
{
  "type": "action_name",
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  },
  "priority": "normal|high|low",
  "timeout": 30000
}
```

### Action Categories

**Movement:**
- `goto` - Navigate to coordinates
- `follow` - Track player/entity
- `come` - Return to sender
- `stop` - Cancel movement

**Interaction:**
- `mine` - Break blocks
- `place` - Place blocks
- `craft` - Use crafting table
- `use` - Use item/block

**Social:**
- `chat` - Send message
- `look_at` - Turn toward target
- `whisper` - Private message

**Information:**
- `inventory` - Check items
- `location` - Report position
- `find` - Search for blocks/entities

### Action Execution Pipeline

```javascript
async function executeAction(action) {
  // 1. Validate action
  if (!isValidAction(action)) {
    return { error: 'Invalid action format' };
  }
  
  // 2. Check preconditions
  if (!canExecute(action)) {
    return { error: 'Cannot execute: preconditions not met' };
  }
  
  // 3. Execute with timeout
  const result = await Promise.race([
    performAction(action),
    timeout(action.timeout || 30000)
  ]);
  
  // 4. Return result to Ollama
  await sendFeedbackToOllama(result);
  
  return result;
}
```

---

## Error Handling & Safety

### Bot Safety Measures

**1. Action Validation**
- Verify coordinates are within reasonable range
- Check inventory before crafting/placing
- Confirm target exists before interaction

**2. Rate Limiting**
- Throttle actions to prevent kicks
- Queue system prevents action spam
- Cooldowns between similar actions

**3. State Monitoring**
```javascript
bot.on('health', () => {
  if (bot.health < 6) {
    bot.pathfinder.setGoal(null); // Stop everything
    bot.chat('Low health! Stopping actions.');
    pauseCommandExecution();
  }
});
```

**4. Stuck Detection**
```javascript
let lastPosition = bot.entity.position.clone();
setInterval(() => {
  if (lastPosition.distanceTo(bot.entity.position) < 0.1) {
    stuckCounter++;
    if (stuckCounter > 50) { // 5 seconds stuck
      bot.pathfinder.setGoal(null);
      sendToOllama("I appear to be stuck");
    }
  } else {
    stuckCounter = 0;
  }
  lastPosition = bot.entity.position.clone();
}, 100);
```

### Ollama Response Validation

**Parse & Verify:**
```javascript
function validateOllamaResponse(response) {
  try {
    const parsed = JSON.parse(response.response);
    
    // Check required fields
    if (!parsed.actions || !Array.isArray(parsed.actions)) {
      return { valid: false, error: 'Missing actions array' };
    }
    
    // Validate each action
    for (const action of parsed.actions) {
      if (!action.type || !VALID_ACTIONS.includes(action.type)) {
        return { valid: false, error: `Invalid action type: ${action.type}` };
      }
    }
    
    return { valid: true, data: parsed };
  } catch (e) {
    return { valid: false, error: 'JSON parse error' };
  }
}
```

### Connection Recovery

```javascript
bot.on('end', () => {
  console.log('Bot disconnected');
  setTimeout(() => {
    console.log('Attempting reconnect...');
    recreateBot();
  }, 5000);
});

bot.on('kicked', (reason) => {
  console.log('Kicked:', reason);
  // Log for debugging anti-cheat issues
});
```

---

## Conclusion

This system creates a powerful interface between AI language models and Minecraft by:

1. **Leveraging Mineflayer** for game interaction
2. **Using Pathfinder** for intelligent navigation
3. **Bridging with Ollama** for natural language understanding
4. **Implementing robust error handling** for stability

The key to success is well-structured command parsing, reliable state management, and comprehensive error handling. Start with basic movement and chat commands, then expand to more complex interactions as the system stabilizes.

### Next Steps

- Set up development environment (Node.js, Ollama)
- Create basic bot with Mineflayer
- Implement simple communication server
- Test with single commands before chaining
- Gradually add action complexity
- Fine-tune Ollama prompts for your use case