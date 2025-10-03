# Ollama Agent + Warudo Avatar Control Guide

A comprehensive guide for connecting an Ollama AI agent to control a virtual avatar in Warudo, enabling real-time animated responses and interactions.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Warudo Installation & Setup](#warudo-installation--setup)
4. [Avatar Model Loading](#avatar-model-loading)
5. [Understanding Warudo's API](#understanding-warudos-api)
6. [Setting Up the Communication Pathway](#setting-up-the-communication-pathway)
7. [Ollama Agent Implementation](#ollama-agent-implementation)
8. [Command Structure](#command-structure)
9. [Animation Control Examples](#animation-control-examples)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This guide demonstrates how to create an AI-powered virtual avatar system where:
- **Ollama** provides the AI agent's intelligence and text generation
- **Warudo** handles avatar rendering and animation
- A **middleware script** bridges communication between both systems

The agent can control facial expressions, body movements, and gestures in response to conversations.

---

## Prerequisites

### Software Requirements
- **Warudo** (v0.12.0 or higher recommended)
- **Ollama** (latest version)
- **Python 3.8+** (for middleware)
- **Node.js 16+** (alternative middleware option)

### Hardware Requirements
- **GPU**: NVIDIA GTX 1060 or better (for Warudo rendering)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB for Warudo + space for avatar models

### Skills Needed
- Basic Python or JavaScript programming
- Understanding of HTTP/REST APIs
- Familiarity with JSON data structures

---

## Warudo Installation & Setup

### Step 1: Download Warudo

1. Visit the official Warudo website: https://warudo.app
2. Purchase or download the appropriate version (Pro recommended for API access)
3. Extract the downloaded archive to your preferred location
4. Launch `Warudo.exe`

### Step 2: Initial Configuration

1. **First Launch**:
   - Complete the initial setup wizard
   - Configure your display settings
   - Set your preferred language

2. **Enable API Access**:
   - Go to `Settings` → `Network`
   - Enable "HTTP API Server"
   - Note the default port (usually `7500`)
   - Set authentication if desired (recommended for security)

3. **Configure Performance**:
   - Go to `Settings` → `Graphics`
   - Adjust quality based on your GPU
   - Enable "Background Rendering" if agent will run continuously

### Step 3: Verify Installation

```bash
# Test if Warudo API is accessible
curl http://localhost:7500/api/status
```

Expected response:
```json
{
  "status": "running",
  "version": "0.12.x"
}
```

---

## Avatar Model Loading

### Supported Avatar Formats

Warudo supports:
- **VRM** (Virtual Reality Model) - Recommended
- **VSFAvatar** (Warudo native format)
- **FBX** with humanoid rig (requires conversion)

### Step 1: Obtaining Avatar Models

**Free Resources**:
- VRoid Hub: https://hub.vroid.com
- Booth.pm: https://booth.pm (search for "VRM")
- VRoid Studio: Create custom avatars

**Commercial Options**:
- Commission custom avatars from artists
- Purchase pre-made models from asset stores

### Step 2: Import Avatar into Warudo

1. **Via GUI**:
   - Click `Assets` → `Character` → `Add Character`
   - Select `Load from VRM file`
   - Navigate to your `.vrm` file
   - Click `Open`

2. **Configure Avatar**:
   - Set default pose
   - Calibrate facial expressions
   - Test basic animations

3. **Save Configuration**:
   - Go to `File` → `Save Scene As`
   - Name your scene (e.g., "OllamaAvatar")
   - This saves avatar and settings

### Step 3: Test Avatar Controls

In Warudo, test these features:
- **Expressions**: Use the expression panel to test facial animations
- **Poses**: Try different idle poses
- **Animations**: Play built-in animation clips

### Step 4: Note Avatar Capabilities

Document what your avatar supports:
- Available facial blend shapes (ARKit, VRM standard, custom)
- Bone structure for procedural animation
- Animation clip names
- Expression presets

---

## Understanding Warudo's API

### API Endpoints Overview

Warudo exposes a REST API on `http://localhost:7500/api/`

#### Key Endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/status` | GET | Check Warudo status |
| `/api/character/list` | GET | List loaded characters |
| `/api/character/{id}/expression` | POST | Set facial expression |
| `/api/character/{id}/animation` | POST | Play animation |
| `/api/character/{id}/pose` | POST | Set bone positions |
| `/api/character/{id}/blend-shapes` | POST | Control blend shapes |
| `/api/scene/load` | POST | Load saved scene |

### API Authentication

If authentication is enabled:

```python
import requests

headers = {
    "Authorization": "Bearer YOUR_API_TOKEN",
    "Content-Type": "application/json"
}

response = requests.get("http://localhost:7500/api/status", headers=headers)
```

### Response Format

All API responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2025-10-03T12:00:00Z"
}
```

---

## Setting Up the Communication Pathway

### Architecture Overview

```
User Input → Ollama Agent → Middleware → Warudo API → Avatar Animation
           ← Response Text ←           ←            ←
```

### Option 1: Python Middleware (Recommended)

#### Install Dependencies

```bash
pip install ollama requests asyncio websockets
```

#### Create Project Structure

```
ollama-warudo/
├── middleware.py       # Main bridge script
├── warudo_client.py    # Warudo API wrapper
├── ollama_agent.py     # Ollama interaction
├── config.json         # Configuration
└── requirements.txt    # Dependencies
```

#### Configuration File (config.json)

```json
{
  "warudo": {
    "host": "localhost",
    "port": 7500,
    "api_token": "YOUR_TOKEN_HERE",
    "character_id": "character_0"
  },
  "ollama": {
    "host": "localhost",
    "port": 11434,
    "model": "llama2",
    "context_length": 4096
  },
  "animation": {
    "idle_expression": "neutral",
    "talking_animation": "talk_01",
    "gesture_enabled": true
  }
}
```

### Option 2: Node.js Middleware

#### Install Dependencies

```bash
npm init -y
npm install axios ollama ws
```

#### Package.json

```json
{
  "name": "ollama-warudo-bridge",
  "version": "1.0.0",
  "dependencies": {
    "axios": "^1.5.0",
    "ollama": "^0.5.0",
    "ws": "^8.14.0"
  }
}
```

---

## Ollama Agent Implementation

### Step 1: Install Ollama

```bash
# Linux/Mac
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

### Step 2: Pull a Model

```bash
# Recommended models for avatar control
ollama pull llama2        # General purpose
ollama pull mistral       # Faster responses
ollama pull neural-chat   # Conversational
```

### Step 3: Test Ollama

```bash
ollama run llama2 "Hello, introduce yourself"
```

### Step 4: Python Implementation

#### ollama_agent.py

```python
import ollama
import json
import re

class OllamaAgent:
    def __init__(self, model="llama2", system_prompt=None):
        self.model = model
        self.conversation_history = []
        
        if system_prompt is None:
            self.system_prompt = """You are a virtual avatar assistant. 
When responding, include emotion and gesture tags to control your avatar:
- [EXPRESSION:happy], [EXPRESSION:sad], [EXPRESSION:surprised], etc.
- [GESTURE:wave], [GESTURE:nod], [GESTURE:think], etc.
- [ANIMATION:celebrate], [ANIMATION:explain], etc.

Example: "Hello! [EXPRESSION:happy] [GESTURE:wave] I'm excited to help you today!"
"""
        else:
            self.system_prompt = system_prompt
    
    def chat(self, user_message):
        """Send message to Ollama and get response with commands"""
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history
            ]
        )
        
        assistant_message = response['message']['content']
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # Parse commands from response
        commands = self.extract_commands(assistant_message)
        clean_text = self.remove_commands(assistant_message)
        
        return {
            "text": clean_text,
            "commands": commands,
            "raw": assistant_message
        }
    
    def extract_commands(self, text):
        """Extract animation commands from text"""
        commands = []
        
        # Find all [TYPE:value] patterns
        pattern = r'\[([A-Z]+):([a-z_]+)\]'
        matches = re.findall(pattern, text)
        
        for cmd_type, cmd_value in matches:
            commands.append({
                "type": cmd_type.lower(),
                "value": cmd_value
            })
        
        return commands
    
    def remove_commands(self, text):
        """Remove command tags from text"""
        return re.sub(r'\[([A-Z]+):([a-z_]+)\]', '', text).strip()
    
    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
```

#### warudo_client.py

```python
import requests
import time

class WarudoClient:
    def __init__(self, host="localhost", port=7500, api_token=None):
        self.base_url = f"http://{host}:{port}/api"
        self.headers = {"Content-Type": "application/json"}
        
        if api_token:
            self.headers["Authorization"] = f"Bearer {api_token}"
        
        self.character_id = None
    
    def get_characters(self):
        """List all loaded characters"""
        response = requests.get(
            f"{self.base_url}/character/list",
            headers=self.headers
        )
        return response.json()
    
    def set_character(self, character_id):
        """Set active character"""
        self.character_id = character_id
    
    def set_expression(self, expression_name, intensity=1.0, duration=0.5):
        """Change facial expression"""
        if not self.character_id:
            raise Exception("No character selected")
        
        payload = {
            "expression": expression_name,
            "intensity": intensity,
            "transition_duration": duration
        }
        
        response = requests.post(
            f"{self.base_url}/character/{self.character_id}/expression",
            json=payload,
            headers=self.headers
        )
        return response.json()
    
    def play_animation(self, animation_name, loop=False):
        """Play animation clip"""
        if not self.character_id:
            raise Exception("No character selected")
        
        payload = {
            "animation": animation_name,
            "loop": loop,
            "blend_time": 0.3
        }
        
        response = requests.post(
            f"{self.base_url}/character/{self.character_id}/animation",
            json=payload,
            headers=self.headers
        )
        return response.json()
    
    def perform_gesture(self, gesture_name):
        """Perform a gesture animation"""
        gesture_map = {
            "wave": "gesture_wave",
            "nod": "gesture_nod",
            "shake_head": "gesture_shake_head",
            "think": "gesture_think",
            "point": "gesture_point"
        }
        
        animation = gesture_map.get(gesture_name, gesture_name)
        return self.play_animation(animation, loop=False)
    
    def set_idle(self):
        """Return to idle state"""
        self.set_expression("neutral")
        self.play_animation("idle", loop=True)
```

#### middleware.py

```python
import asyncio
import json
from ollama_agent import OllamaAgent
from warudo_client import WarudoClient

class AvatarMiddleware:
    def __init__(self, config_path="config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize Ollama agent
        self.agent = OllamaAgent(
            model=self.config['ollama']['model']
        )
        
        # Initialize Warudo client
        self.warudo = WarudoClient(
            host=self.config['warudo']['host'],
            port=self.config['warudo']['port'],
            api_token=self.config['warudo'].get('api_token')
        )
        
        # Set character
        self.warudo.set_character(self.config['warudo']['character_id'])
    
    async def process_message(self, user_input):
        """Process user message and animate avatar"""
        print(f"User: {user_input}")
        
        # Get response from Ollama
        response = self.agent.chat(user_input)
        
        print(f"Avatar: {response['text']}")
        
        # Execute animation commands
        await self.execute_commands(response['commands'])
        
        return response['text']
    
    async def execute_commands(self, commands):
        """Execute animation commands in Warudo"""
        for cmd in commands:
            try:
                if cmd['type'] == 'expression':
                    self.warudo.set_expression(cmd['value'])
                    await asyncio.sleep(0.1)
                
                elif cmd['type'] == 'gesture':
                    self.warudo.perform_gesture(cmd['value'])
                    await asyncio.sleep(0.5)
                
                elif cmd['type'] == 'animation':
                    self.warudo.play_animation(cmd['value'])
                    await asyncio.sleep(0.3)
                
            except Exception as e:
                print(f"Error executing command {cmd}: {e}")
    
    async def run_interactive(self):
        """Run interactive chat loop"""
        print("Avatar Agent Ready! Type 'quit' to exit.")
        self.warudo.set_idle()
        
        while True:
            user_input = input("\nYou: ")
            
            if user_input.lower() in ['quit', 'exit']:
                self.warudo.set_idle()
                break
            
            await self.process_message(user_input)

# Main execution
if __name__ == "__main__":
    middleware = AvatarMiddleware()
    asyncio.run(middleware.run_interactive())
```

---

## Command Structure

### Expression Commands

```python
# Basic expressions
expressions = {
    "neutral": "Default/resting face",
    "happy": "Smile, raised cheeks",
    "sad": "Frown, lowered brows",
    "angry": "Furrowed brows, tense",
    "surprised": "Wide eyes, open mouth",
    "disgusted": "Wrinkled nose, squint",
    "fearful": "Wide eyes, tension",
    "thinking": "Slight squint, raised brow"
}

# Usage
warudo.set_expression("happy", intensity=0.8)
```

### Gesture Commands

```python
# Common gestures
gestures = {
    "wave": "Hand wave greeting",
    "nod": "Head nod (yes)",
    "shake_head": "Head shake (no)",
    "shrug": "Shoulder shrug",
    "point": "Point forward",
    "think": "Hand on chin",
    "crossed_arms": "Arms crossed"
}

# Usage
warudo.perform_gesture("wave")
```

### Animation Commands

```python
# Full body animations
animations = {
    "idle": "Standing idle loop",
    "talk_01": "Talking animation 1",
    "talk_02": "Talking animation 2",
    "celebrate": "Celebration pose",
    "bow": "Respectful bow",
    "sit": "Sitting pose",
    "walk": "Walking cycle"
}

# Usage
warudo.play_animation("celebrate", loop=False)
```

---

## Animation Control Examples

### Example 1: Simple Greeting

```python
async def greeting_sequence():
    # Wave and smile
    warudo.set_expression("happy", intensity=1.0)
    warudo.perform_gesture("wave")
    await asyncio.sleep(2)
    
    # Return to neutral
    warudo.set_expression("neutral")
    warudo.set_idle()
```

### Example 2: Emotional Response

```python
async def emotional_response(emotion):
    emotion_map = {
        "joy": ("happy", "celebrate"),
        "sadness": ("sad", None),
        "surprise": ("surprised", None),
        "anger": ("angry", "crossed_arms")
    }
    
    expression, gesture = emotion_map.get(emotion, ("neutral", None))
    
    warudo.set_expression(expression, intensity=0.9)
    if gesture:
        warudo.perform_gesture(gesture)
    
    await asyncio.sleep(3)
    warudo.set_idle()
```

### Example 3: Context-Aware Animation

```python
async def context_animation(text, sentiment):
    # Start with base expression
    if sentiment > 0.5:
        warudo.set_expression("happy")
    elif sentiment < -0.5:
        warudo.set_expression("sad")
    else:
        warudo.set_expression("neutral")
    
    # Add gestures based on keywords
    if "hello" in text.lower() or "hi" in text.lower():
        warudo.perform_gesture("wave")
    elif "?" in text:
        warudo.perform_gesture("think")
    elif "!" in text and sentiment > 0:
        warudo.perform_gesture("celebrate")
    
    # Play talking animation during speech
    warudo.play_animation("talk_01", loop=False)
```

### Example 4: Multi-Step Sequence

```python
async def explain_something():
    # Thinking phase
    warudo.set_expression("thinking")
    warudo.perform_gesture("think")
    await asyncio.sleep(1.5)
    
    # Explanation phase
    warudo.set_expression("neutral")
    warudo.perform_gesture("point")
    warudo.play_animation("talk_02", loop=False)
    await asyncio.sleep(3)
    
    # Confirmation phase
    warudo.set_expression("happy")
    warudo.perform_gesture("nod")
    await asyncio.sleep(1)
    
    # Return to idle
    warudo.set_idle()
```

---

## Troubleshooting

### Warudo Connection Issues

**Problem**: Cannot connect to Warudo API

**Solutions**:
1. Verify Warudo is running
2. Check API is enabled in Settings → Network
3. Confirm port 7500 is not blocked by firewall
4. Test with: `curl http://localhost:7500/api/status`

**Problem**: Authentication errors

**Solutions**:
1. Verify API token is correct in config.json
2. Check token hasn't expired
3. Regenerate token in Warudo settings

### Ollama Issues

**Problem**: Ollama not responding

**Solutions**:
```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
# Linux/Mac
systemctl restart ollama

# Windows
# Restart from Services or Task Manager
```

**Problem**: Model not found

**Solutions**:
```bash
# List available models
ollama list

# Pull required model
ollama pull llama2
```

### Animation Issues

**Problem**: Expressions not changing

**Solutions**:
1. Verify character_id is correct
2. Check avatar has blend shapes
3. Ensure expression names match avatar's capabilities
4. Test manually in Warudo GUI first

**Problem**: Gestures not playing

**Solutions**:
1. Confirm animation clips exist for your avatar
2. Check animation names in Warudo's animation list
3. Verify character has necessary bones
4. Increase blend_time for smoother transitions

### Performance Issues

**Problem**: Slow response times

**Solutions**:
1. Use smaller Ollama model (e.g., mistral instead of llama2)
2. Reduce Warudo graphics quality
3. Limit conversation history length
4. Use async/await properly to prevent blocking

**Problem**: Animation lag

**Solutions**:
1. Reduce transition_duration in expressions
2. Preload common animations
3. Optimize Warudo scene (remove unused assets)
4. Check GPU usage and temperature

### Common Errors

```python
# Error: Character not found
# Solution: Get correct character ID
characters = warudo.get_characters()
print(characters)  # Use correct ID from here

# Error: Invalid expression name
# Solution: List available expressions
# In Warudo GUI, check character's blend shapes

# Error: Connection timeout
# Solution: Increase timeout
response = requests.post(url, json=data, timeout=10)
```

---

## Advanced Features

### Voice Synthesis Integration

```python
# Add TTS for voice output
import pyttsx3

class VoiceAvatar(AvatarMiddleware):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tts = pyttsx3.init()
    
    async def process_message(self, user_input):
        response = await super().process_message(user_input)
        
        # Speak while animating
        self.warudo.play_animation("talk_01", loop=True)
        self.tts.say(response)
        self.tts.runAndWait()
        self.warudo.set_idle()
        
        return response
```

### Sentiment Analysis

```python
from textblob import TextBlob

def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity  # -1 to 1

async def process_with_sentiment(user_input):
    sentiment = analyze_sentiment(user_input)
    
    # Adjust avatar emotion based on user sentiment
    if sentiment > 0.3:
        warudo.set_expression("happy")
    elif sentiment < -0.3:
        warudo.set_expression("sad")
    else:
        warudo.set_expression("neutral")
    
    response = agent.chat(user_input)
    return response
```

### Web Interface

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
middleware = AvatarMiddleware()

@app.route('/chat', methods=['POST'])
async def chat():
    data = request.json
    response = await middleware.process_message(data['message'])
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(port=5000)
```

---

## Best Practices

1. **Error Handling**: Always wrap API calls in try-except blocks
2. **Rate Limiting**: Don't send commands faster than avatar can execute
3. **State Management**: Track current expression/animation to avoid conflicts
4. **Resource Cleanup**: Properly close connections and reset state
5. **Testing**: Test each animation individually before complex sequences
6. **Documentation**: Document your avatar's specific capabilities
7. **Performance**: Profile and optimize bottlenecks
8. **Security**: Never expose API tokens in code; use environment variables

---

## Resources

- **Warudo Documentation**: https://docs.warudo.app
- **Ollama Documentation**: https://ollama.ai/docs
- **VRM Specification**: https://vrm.dev
- **Community Discord**: Check Warudo's official community for support

---

## License & Credits

This guide is provided as-is for educational purposes. Ensure you comply with:
- Warudo's license terms
- Avatar model licenses
- Ollama's usage terms

Created for the AI avatar development community. Contributions welcome!