# YouTube Live Chat Integration for Ollama - Complete Guide

This guide walks you through building a system that fetches YouTube livestream chat messages and provides them as context to a local Ollama AI model.

## Overview

The system consists of three main components:
1. **Chat Monitor** - Fetches messages from YouTube's live chat API
2. **Context Manager** - Formats chat messages for AI consumption
3. **Ollama Integration** - Sends chat context to your local AI model

## Prerequisites

- Python 3.7+
- A running Ollama instance with a model installed
- Required Python package: `requests`

```bash
pip install requests
```

## How YouTube Live Chat Works

YouTube uses an internal API endpoint that requires:
1. A **continuation token** extracted from the livestream page
2. Periodic polling of the chat endpoint with this token
3. Each response contains new messages and an updated continuation token

## Implementation

### Step 1: Create the Chat Monitor Class

```python
import time
import threading
import requests
import re
from datetime import datetime
from typing import Optional, Callable, List, Dict

class YouTubeChatMonitor:
    """Monitor YouTube live chat using direct API calls"""
    
    def __init__(self, video_id: str, max_messages: int = 50):
        self.video_id = video_id
        self.max_messages = max_messages
        self.chat_buffer: List[Dict] = []
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.session = None
        
        # Chat API state
        self.continuation_token = None
        self.polling_interval = 2.0
```

### Step 2: Extract the Continuation Token

The continuation token is embedded in the livestream page HTML:

```python
    def _extract_continuation_token(self) -> Optional[str]:
        """Extract live chat continuation token from video page"""
        try:
            url = f"https://www.youtube.com/watch?v={self.video_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Search for continuation patterns in the HTML
            patterns = [
                r'"liveChatRenderer":\{"continuations":\[\{"reloadContinuationData":\{"continuation":"([^"]+)"',
                r'continuation":"([A-Za-z0-9_-]{100,})"'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    return match.group(1)
            
            print("Could not find live chat - stream may not be live or chat is disabled")
            return None
            
        except Exception as e:
            print(f"Error extracting continuation token: {e}")
            return None
```

### Step 3: Fetch Chat Messages

Use YouTube's internal API to fetch messages:

```python
    def _fetch_messages(self) -> List[Dict]:
        """Fetch new chat messages"""
        if not self.continuation_token:
            return []
        
        try:
            url = "https://www.youtube.com/youtubei/v1/live_chat/get_live_chat"
            
            payload = {
                "context": {
                    "client": {
                        "clientName": "WEB",
                        "clientVersion": "2.20231201.00.00"
                    }
                },
                "continuation": self.continuation_token
            }
            
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse messages
            messages = []
            continuation_contents = data.get("continuationContents", {})
            live_chat = continuation_contents.get("liveChatContinuation", {})
            
            # Extract chat messages
            for action in live_chat.get("actions", []):
                item = action.get("addChatItemAction", {}).get("item", {})
                text_message = item.get("liveChatTextMessageRenderer", {})
                
                if text_message:
                    author = text_message.get("authorName", {}).get("simpleText", "Unknown")
                    message_runs = text_message.get("message", {}).get("runs", [])
                    message_text = "".join(part.get("text", "") for part in message_runs)
                    timestamp = int(text_message.get("timestampUsec", str(int(time.time() * 1000000)))) // 1000
                    
                    messages.append({
                        'author': author,
                        'message': message_text,
                        'timestamp': timestamp
                    })
            
            # Update continuation token for next request
            for cont in live_chat.get("continuations", []):
                if "invalidationContinuationData" in cont:
                    self.continuation_token = cont["invalidationContinuationData"]["continuation"]
                    timeout_ms = cont["invalidationContinuationData"].get("timeoutDurationMillis", 2000)
                    self.polling_interval = max(timeout_ms / 1000, 1.0)
                    break
            
            return messages
            
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return []
```

### Step 4: Implement the Monitoring Loop

```python
    def start(self):
        """Start monitoring the live chat"""
        if self.running:
            return False
        
        # Create session with browser-like headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        # Get initial continuation token
        self.continuation_token = self._extract_continuation_token()
        if not self.continuation_token:
            return False
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        return True
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                messages = self._fetch_messages()
                
                # Add to buffer
                for msg in messages:
                    self.chat_buffer.append(msg)
                
                # Keep only recent messages
                if len(self.chat_buffer) > self.max_messages:
                    self.chat_buffer = self.chat_buffer[-self.max_messages:]
                
                time.sleep(self.polling_interval)
                
            except Exception as e:
                print(f"Monitor loop error: {e}")
                time.sleep(5)
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=3.0)
        if self.session:
            self.session.close()
    
    def get_recent_messages(self, count: Optional[int] = None) -> List[Dict]:
        """Get recent messages from buffer"""
        if not self.chat_buffer:
            return []
        return self.chat_buffer[-(count or len(self.chat_buffer)):]
```

### Step 5: Format Chat for Ollama

Create a helper function to format chat messages for AI context:

```python
def format_chat_for_ollama(messages: List[Dict]) -> str:
    """Format chat messages as context for Ollama"""
    if not messages:
        return "No recent chat messages."
    
    formatted = "Recent YouTube Live Chat:\n\n"
    for msg in messages:
        formatted += f"{msg['author']}: {msg['message']}\n"
    
    return formatted
```

### Step 6: Integrate with Ollama

```python
import json

def query_ollama_with_chat(model: str, user_prompt: str, chat_messages: List[Dict], 
                           system_prompt: str = "You are a helpful AI assistant."):
    """Send a query to Ollama with chat context"""
    
    # Format chat messages as context
    chat_context = format_chat_for_ollama(chat_messages)
    
    # Build the full prompt
    full_prompt = f"""{system_prompt}

{chat_context}

User: {user_prompt}
Assistant:"""
    
    # Call Ollama API
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": full_prompt,
            "stream": False
        }
    )
    
    if response.status_code == 200:
        return response.json()["response"]
    else:
        return f"Error: {response.status_code}"
```

## Complete Example Usage

```python
def main():
    # Replace with your YouTube video ID
    VIDEO_ID = "dQw4w9WgXcQ"
    
    # Initialize chat monitor
    print("Starting YouTube chat monitor...")
    monitor = YouTubeChatMonitor(video_id=VIDEO_ID, max_messages=50)
    
    if not monitor.start():
        print("Failed to start chat monitor")
        return
    
    print("Chat monitor started. Waiting for messages...")
    time.sleep(10)  # Let some messages accumulate
    
    try:
        while True:
            # Get recent messages
            recent_messages = monitor.get_recent_messages(count=20)
            
            if recent_messages:
                # Example: Ask Ollama to summarize the chat
                response = query_ollama_with_chat(
                    model="llama3.2",
                    user_prompt="Summarize what viewers are talking about",
                    chat_messages=recent_messages,
                    system_prompt="You are analyzing YouTube live chat."
                )
                
                print("\n=== AI Analysis ===")
                print(response)
                print("==================\n")
            
            time.sleep(30)  # Query every 30 seconds
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        monitor.stop()

if __name__ == "__main__":
    main()
```

## Advanced: Streaming Responses

For streaming responses from Ollama:

```python
def stream_ollama_with_chat(model: str, user_prompt: str, chat_messages: List[Dict]):
    """Stream Ollama response with chat context"""
    chat_context = format_chat_for_ollama(chat_messages)
    full_prompt = f"Recent chat context:\n{chat_context}\n\nUser: {user_prompt}\nAssistant:"
    
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": full_prompt, "stream": True},
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            chunk = json.loads(line)
            if not chunk.get("done"):
                print(chunk.get("response", ""), end="", flush=True)
    print()
```

## Use Cases

### 1. Interactive Streamer Assistant
Monitor chat and respond to common questions:

```python
def chatbot_loop(monitor, model="llama3.2"):
    while True:
        messages = monitor.get_recent_messages(20)
        
        # Check for questions
        for msg in messages[-5:]:  # Check last 5 messages
            if "?" in msg['message']:
                response = query_ollama_with_chat(
                    model=model,
                    user_prompt=f"Answer this viewer question: {msg['message']}",
                    chat_messages=messages
                )
                print(f"Response to {msg['author']}: {response}")
        
        time.sleep(10)
```

### 2. Chat Sentiment Analysis

```python
def analyze_sentiment(monitor):
    messages = monitor.get_recent_messages(50)
    
    response = query_ollama_with_chat(
        model="llama3.2",
        user_prompt="Analyze the overall sentiment and mood of these chat messages. Are viewers happy, excited, confused, or frustrated?",
        chat_messages=messages,
        system_prompt="You are a sentiment analysis expert."
    )
    
    return response
```

### 3. Topic Detection

```python
def detect_topics(monitor):
    messages = monitor.get_recent_messages(100)
    
    response = query_ollama_with_chat(
        model="llama3.2",
        user_prompt="What are the top 3 topics viewers are discussing? List them with brief explanations.",
        chat_messages=messages
    )
    
    return response
```

## Troubleshooting

### Chat Monitor Won't Start
- Verify the video is actually live (not a premiere or regular video)
- Check if chat is enabled on the stream
- Ensure you have a stable internet connection

### No Messages Appearing
- Wait 30-60 seconds after starting (messages may be delayed)
- Verify the stream has active chat participants
- Check console for error messages

### Rate Limiting
- YouTube may rate limit excessive requests
- Keep polling interval at 2+ seconds
- Don't run multiple monitors simultaneously

### Ollama Connection Issues
- Verify Ollama is running: `ollama list`
- Check the API endpoint: `http://localhost:11434/api/generate`
- Test with: `curl http://localhost:11434/api/version`

## Performance Optimization

### Memory Management
```python
# Limit buffer size aggressively for long streams
monitor = YouTubeChatMonitor(video_id=VIDEO_ID, max_messages=30)
```

### Reduce Ollama Processing
```python
# Only process every N messages
message_count = 0
threshold = 10

for msg in monitor.get_recent_messages():
    message_count += 1
    if message_count >= threshold:
        # Process with Ollama
        message_count = 0
```

## Security Considerations

- Never expose continuation tokens publicly
- Run on trusted networks only
- Implement rate limiting for production use
- Sanitize chat messages before displaying (remove malicious links)
- Consider implementing profanity filters

## Next Steps

- Add message filtering (keywords, user roles)
- Implement chat command system
- Store chat history in database
- Create web dashboard for monitoring
- Add text-to-speech for AI responses
- Implement multi-stream monitoring

## License and Legal

This implementation uses YouTube's publicly accessible APIs. Ensure compliance with:
- YouTube Terms of Service
- API usage guidelines
- Respect user privacy and chat moderation settings

---

**Note**: This guide provides educational content for building personal projects. For production use, consider YouTube's official Data API v3 with proper authentication.