# Vosk + Ollama Voice-to-Text Setup Guide

## Overview

This guide demonstrates how to set up Vosk (offline speech recognition) to capture voice input and send it as text prompts to Ollama for AI-powered responses.

## Prerequisites

- Python 3.7 or higher
- Ollama installed and running locally
- Microphone access
- 2-3 GB free disk space for Vosk models

## Part 1: Installation

### 1.1 Install Required Python Packages

```bash
pip install vosk sounddevice numpy ollama
```

**Package purposes:**
- `vosk`: Offline speech recognition engine
- `sounddevice`: Audio capture from microphone
- `numpy`: Audio data processing
- `ollama`: Python client for Ollama API

### 1.2 Download Vosk Model

Vosk models are available at: https://alphacephei.com/vosk/models

**Recommended models:**

| Model | Size | Language | Best For |
|-------|------|----------|----------|
| vosk-model-small-en-us-0.15 | 40 MB | English | Fast, basic accuracy |
| vosk-model-en-us-0.22 | 1.8 GB | English | High accuracy, general use |
| vosk-model-en-us-0.22-lgraph | 128 MB | English | Good balance |

**Download and extract:**

```bash
# Example for small English model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

Or manually download from the website and extract to your project directory.

### 1.3 Install and Start Ollama

```bash
# Download Ollama from https://ollama.ai
# Then pull a model (e.g., llama2)
ollama pull llama2
```

## Part 2: Basic Implementation

### 2.1 Simple Voice-to-Text Test

Create `test_vosk.py`:

```python
import vosk
import sounddevice as sd
import json
import queue

# Configuration
MODEL_PATH = "vosk-model-small-en-us-0.15"
SAMPLE_RATE = 16000

# Initialize model
model = vosk.Model(MODEL_PATH)
recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)

# Audio queue for processing
audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    """Callback function for audio stream"""
    if status:
        print(f"Audio status: {status}")
    audio_queue.put(bytes(indata))

print("Listening... Speak into your microphone (Ctrl+C to stop)")

# Start audio stream
with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, 
                       dtype='int16', channels=1, 
                       callback=audio_callback):
    while True:
        data = audio_queue.get()
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get('text', '')
            if text:
                print(f"Recognized: {text}")
```

### 2.2 Full Voice-to-Ollama Integration

Create `voice_ollama.py`:

```python
import vosk
import sounddevice as sd
import json
import queue
import ollama
import sys
from typing import Optional

class VoiceToOllama:
    def __init__(self, model_path: str, ollama_model: str = "llama2", 
                 sample_rate: int = 16000):
        """
        Initialize Voice-to-Ollama system
        
        Args:
            model_path: Path to Vosk model directory
            ollama_model: Name of Ollama model to use
            sample_rate: Audio sample rate (Hz)
        """
        self.sample_rate = sample_rate
        self.ollama_model = ollama_model
        self.audio_queue = queue.Queue()
        
        # Initialize Vosk
        print(f"Loading Vosk model from {model_path}...")
        self.model = vosk.Model(model_path)
        self.recognizer = vosk.KaldiRecognizer(self.model, sample_rate)
        self.recognizer.SetWords(True)  # Get word-level timestamps
        
        print(f"Using Ollama model: {ollama_model}")
        
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            print(f"Audio error: {status}", file=sys.stderr)
        self.audio_queue.put(bytes(indata))
    
    def listen_for_speech(self, timeout: Optional[float] = None) -> str:
        """
        Listen for speech and return transcribed text
        
        Args:
            timeout: Maximum seconds to listen (None = indefinite)
            
        Returns:
            Transcribed text string
        """
        print("🎤 Listening... (speak now)")
        transcribed_text = ""
        
        with sd.RawInputStream(samplerate=self.sample_rate, 
                              blocksize=8000,
                              dtype='int16', 
                              channels=1,
                              callback=self.audio_callback):
            while True:
                data = self.audio_queue.get()
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').strip()
                    
                    if text:
                        transcribed_text = text
                        print(f"📝 Transcribed: {text}")
                        break
        
        return transcribed_text
    
    def send_to_ollama(self, prompt: str, stream: bool = True) -> str:
        """
        Send prompt to Ollama and get response
        
        Args:
            prompt: Text prompt for Ollama
            stream: Whether to stream response
            
        Returns:
            Ollama's response text
        """
        print(f"\n🤖 Sending to {self.ollama_model}...\n")
        
        response_text = ""
        
        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=stream
            )
            
            if stream:
                for chunk in response:
                    content = chunk['message']['content']
                    print(content, end='', flush=True)
                    response_text += content
                print("\n")
            else:
                response_text = response['message']['content']
                print(response_text)
                
        except Exception as e:
            print(f"Error communicating with Ollama: {e}")
            
        return response_text
    
    def run_interactive(self):
        """Run interactive voice-to-AI loop"""
        print("\n" + "="*60)
        print("Voice-to-Ollama Interactive Mode")
        print("="*60)
        print("Commands:")
        print("  - Speak your question/prompt")
        print("  - Say 'exit' or 'quit' to stop")
        print("  - Press Ctrl+C to force quit")
        print("="*60 + "\n")
        
        try:
            while True:
                # Listen for voice input
                text = self.listen_for_speech()
                
                if not text:
                    print("⚠️  No speech detected. Please try again.")
                    continue
                
                # Check for exit commands
                if text.lower() in ['exit', 'quit', 'stop', 'goodbye']:
                    print("👋 Goodbye!")
                    break
                
                # Send to Ollama
                self.send_to_ollama(text)
                print("\n" + "-"*60 + "\n")
                
        except KeyboardInterrupt:
            print("\n\n👋 Session ended by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")

def main():
    # Configuration
    VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"
    OLLAMA_MODEL = "llama2"  # Change to your preferred model
    
    # Initialize and run
    voice_system = VoiceToOllama(
        model_path=VOSK_MODEL_PATH,
        ollama_model=OLLAMA_MODEL
    )
    
    voice_system.run_interactive()

if __name__ == "__main__":
    main()
```

## Part 3: Advanced Features

### 3.1 Continuous Listening with Wake Word

Create `voice_ollama_wakework.py`:

```python
import vosk
import sounddevice as sd
import json
import queue
import ollama

class WakeWordVoiceSystem:
    def __init__(self, model_path: str, wake_word: str = "computer"):
        self.wake_word = wake_word.lower()
        self.sample_rate = 16000
        self.audio_queue = queue.Queue()
        
        self.model = vosk.Model(model_path)
        self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
        
    def audio_callback(self, indata, frames, time, status):
        self.audio_queue.put(bytes(indata))
    
    def listen_continuous(self):
        """Continuously listen for wake word"""
        print(f"👂 Listening for wake word: '{self.wake_word}'...")
        
        with sd.RawInputStream(samplerate=self.sample_rate,
                              blocksize=8000,
                              dtype='int16',
                              channels=1,
                              callback=self.audio_callback):
            while True:
                data = self.audio_queue.get()
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').lower()
                    
                    if self.wake_word in text:
                        print(f"✓ Wake word detected!")
                        # Get the actual command after wake word
                        command = self.get_command()
                        if command:
                            self.process_command(command)
    
    def get_command(self) -> str:
        """Get command after wake word"""
        print("🎤 Listening for command...")
        
        # Reset recognizer for new command
        self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
        
        command_duration = 0
        max_duration = 5  # seconds
        
        while command_duration < max_duration:
            data = self.audio_queue.get()
            
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get('text', '').strip()
                if text:
                    return text
            
            command_duration += 0.5  # approximate
        
        return ""
    
    def process_command(self, command: str):
        """Send command to Ollama"""
        print(f"📝 Command: {command}\n")
        
        response = ollama.chat(
            model='llama2',
            messages=[{'role': 'user', 'content': command}],
            stream=True
        )
        
        print("🤖 Response: ", end='')
        for chunk in response:
            print(chunk['message']['content'], end='', flush=True)
        print("\n" + "="*60 + "\n")

# Usage
if __name__ == "__main__":
    system = WakeWordVoiceSystem(
        model_path="vosk-model-small-en-us-0.15",
        wake_word="computer"
    )
    system.listen_continuous()
```

### 3.2 Audio Quality Configuration

```python
# Add these settings to improve recognition

# For noisy environments
recognizer.SetMaxAlternatives(3)  # Get multiple alternatives
recognizer.SetWords(True)  # Get word-level confidence

# Adjust microphone settings
sd.default.samplerate = 16000
sd.default.channels = 1
sd.default.dtype = 'int16'

# Check available audio devices
print(sd.query_devices())

# Use specific device
device_id = 0  # Change based on your setup
with sd.RawInputStream(samplerate=16000, device=device_id, ...):
    pass
```

## Part 4: Troubleshooting

### Common Issues

**1. "No such file or directory" - Model not found**
```bash
# Verify model path
ls vosk-model-*
# Update MODEL_PATH in your script
```

**2. "PortAudio error" - Microphone access**
```bash
# Linux: Install PortAudio
sudo apt-get install portaudio19-dev python3-pyaudio

# macOS: Grant microphone permissions
# System Preferences > Security & Privacy > Microphone
```

**3. Poor recognition accuracy**
- Use a larger Vosk model (vosk-model-en-us-0.22)
- Reduce background noise
- Speak clearly and at moderate pace
- Adjust microphone closer to mouth
- Check microphone input level

**4. Ollama connection error**
```bash
# Verify Ollama is running
ollama list

# Start Ollama service
ollama serve

# Check if model exists
ollama pull llama2
```

**5. High CPU usage**
- Use smaller Vosk model for lower resource usage
- Reduce audio sample rate (but may decrease accuracy)
- Use smaller Ollama model (e.g., llama2:7b instead of llama2:13b)

## Part 5: Best Practices

### Performance Optimization

1. **Model Selection**
   - Development: Use small models (40-128 MB)
   - Production: Use large models (1.8 GB) for accuracy

2. **Resource Management**
   - Load models once at startup
   - Reuse recognizer instances when possible
   - Clear audio queue periodically

3. **Error Handling**
```python
try:
    text = self.listen_for_speech()
except Exception as e:
    print(f"Error: {e}")
    # Fallback to text input
    text = input("Voice failed. Type your message: ")
```

### Privacy Considerations

- **Vosk is fully offline** - no data sent to cloud
- Audio is processed locally in real-time
- Transcribed text is sent to Ollama (also local)
- No recordings saved by default

### Enhancement Ideas

1. **Add conversation history**
```python
conversation_history = []

def send_to_ollama_with_history(self, prompt: str):
    conversation_history.append({'role': 'user', 'content': prompt})
    
    response = ollama.chat(
        model=self.ollama_model,
        messages=conversation_history,
        stream=True
    )
    # Add response to history...
```

2. **Save transcriptions**
```python
with open('transcripts.txt', 'a') as f:
    f.write(f"{timestamp}: {transcribed_text}\n")
```

3. **Add voice output (text-to-speech)**
```bash
pip install pyttsx3
```

```python
import pyttsx3

engine = pyttsx3.init()
engine.say(ollama_response)
engine.runAndWait()
```

## Part 6: Example Use Cases

### Use Case 1: Voice-Controlled Coding Assistant

```python
system = VoiceToOllama(
    model_path="vosk-model-en-us-0.22",
    ollama_model="codellama"
)

# Ask: "Write a Python function to sort a list"
```

### Use Case 2: Voice Note-Taking

```python
# Speak notes and have AI summarize/organize them
text = voice_system.listen_for_speech()
summary = voice_system.send_to_ollama(
    f"Summarize these notes in bullet points: {text}"
)
```

### Use Case 3: Accessibility Tool

```python
# Help users with limited typing ability
# Hands-free computer interaction
```

## Resources

- **Vosk**: https://alphacephei.com/vosk/
- **Vosk Models**: https://alphacephei.com/vosk/models
- **Ollama**: https://ollama.ai
- **Ollama Models**: https://ollama.ai/library
- **sounddevice docs**: https://python-sounddevice.readthedocs.io/

## Quick Start Command Summary

```bash
# Install dependencies
pip install vosk sounddevice numpy ollama

# Download Vosk model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip

# Install and start Ollama
ollama pull llama2

# Run the script
python voice_ollama.py
```

---

**Happy voice-powered AI interactions!** 🎤🤖