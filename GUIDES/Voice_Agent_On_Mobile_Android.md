# Voice Interface Guide: TTS and Voice Input for Ollama on Android

## Overview

This guide will help you add voice capabilities to your Ollama setup on Android using Termux. You'll be able to speak to your AI assistant and hear its responses, creating a more natural interaction experience.

## What You'll Build

- **Voice Input**: Speak your questions using Vosk (offline speech recognition)
- **Text-to-Speech**: Hear Ollama's responses using pyttsx3 and eSpeak
- **Complete Voice Loop**: Hands-free conversation with your AI

---

## Prerequisites

Before starting this guide, you must have:
- ✅ Termux installed (from F-Droid, not Play Store)
- ✅ Ubuntu installed via proot-distro
- ✅ Ollama installed and working
- ✅ At least one model downloaded (e.g., phi, llama2, mistral)

If you haven't completed these steps, refer to the main Ollama setup guide first.

---

## Part 1: Installing Dependencies

### Step 1: Access Ubuntu Environment

Open Termux and login to Ubuntu:
```bash
proot-distro login ubuntu
```

### Step 2: Install System Dependencies

```bash
apt update
apt install -y python3 python3-pip portaudio19-dev python3-pyaudio espeak ffmpeg
```

**What each package does:**
- **python3**: Programming language for our scripts
- **python3-pip**: Python package installer
- **portaudio19-dev**: Audio I/O library (required for PyAudio)
- **python3-pyaudio**: Python audio library for recording
- **espeak**: Text-to-speech engine
- **ffmpeg**: Audio processing (helps with format conversion)

### Step 3: Install Python Libraries

```bash
pip3 install pyttsx3 vosk sounddevice numpy requests
```

**What each library does:**
- **pyttsx3**: Text-to-speech library (works with eSpeak)
- **vosk**: Offline speech recognition
- **sounddevice**: Audio recording
- **numpy**: Numerical operations (required by audio processing)
- **requests**: HTTP library for communicating with Ollama

---

## Part 2: Download Vosk Language Model

Vosk requires a language model for speech recognition. We'll use a small English model.

### Step 1: Create Directory for Models

```bash
mkdir -p ~/vosk-models
cd ~/vosk-models
```

### Step 2: Download Small English Model

```bash
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
```

**Size:** ~40MB (there are larger, more accurate models available)

### Step 3: Extract the Model

```bash
apt install -y unzip
unzip vosk-model-small-en-us-0.15.zip
```

**Alternative models** (larger = more accurate, but slower):
- `vosk-model-en-us-0.22` (~1.8GB) - High accuracy
- `vosk-model-en-us-0.22-lgraph` (~128MB) - Medium accuracy

---

## Part 3: Test TTS (Text-to-Speech)

Let's verify that eSpeak is working.

### Test eSpeak Directly

```bash
espeak "Hello, I am your AI assistant"
```

**Expected result:** You should hear the synthesized voice through your phone's speaker.

**Troubleshooting:**
- If no sound: Check your phone's volume
- If error: Make sure espeak is installed: `apt install espeak`

---

## Part 4: Create the Voice Interface Script

### Step 1: Create Working Directory

```bash
mkdir -p ~/ollama-voice
cd ~/ollama-voice
```

### Step 2: Create the Main Script

Create a file called `voice_chat.py`:

```bash
nano voice_chat.py
```

**Note:** In nano editor:
- Type or paste the code
- Press `Ctrl + X` to exit
- Press `Y` to save
- Press `Enter` to confirm filename

### Step 3: Paste This Code

```python
#!/usr/bin/env python3
"""
Voice Chat with Ollama
Speak to your AI and hear responses
"""

import json
import queue
import sys
import sounddevice as sd
import vosk
import pyttsx3
import requests
from threading import Thread

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi"  # Change this to your model (llama2, mistral, etc.)
VOSK_MODEL_PATH = "/root/vosk-models/vosk-model-small-en-us-0.15"
SAMPLE_RATE = 16000

# Initialize TTS
print("Initializing text-to-speech...")
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Speed of speech
engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)

# Initialize speech recognition
print("Loading speech recognition model...")
try:
    model = vosk.Model(VOSK_MODEL_PATH)
    recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    print("✓ Speech recognition ready")
except Exception as e:
    print(f"Error loading Vosk model: {e}")
    print(f"Make sure the model exists at: {VOSK_MODEL_PATH}")
    sys.exit(1)

# Audio queue for processing
audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    """Callback for audio stream"""
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))

def speak(text):
    """Convert text to speech"""
    print(f"\n🤖 Assistant: {text}\n")
    engine.say(text)
    engine.runAndWait()

def get_ollama_response(prompt):
    """Send prompt to Ollama and get response"""
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
        
        print("🤔 Thinking...")
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', 'I could not generate a response.')
        else:
            return f"Error: Server returned status code {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Make sure it's running with 'ollama serve'"
    except Exception as e:
        return f"Error: {str(e)}"

def listen():
    """Listen for voice input and return transcribed text"""
    print("\n🎤 Listening... (speak now, pause when done)")
    
    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, 
                          dtype='int16', channels=1, 
                          callback=audio_callback):
        
        silence_threshold = 30  # Frames of silence before stopping
        silence_count = 0
        
        while True:
            try:
                data = audio_queue.get(timeout=1)
                
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get('text', '')
                    
                    if text:
                        silence_count = 0
                        return text
                else:
                    # Partial result (while speaking)
                    partial = json.loads(recognizer.PartialResult())
                    partial_text = partial.get('partial', '')
                    
                    if partial_text:
                        print(f"\r📝 {partial_text}", end='', flush=True)
                        silence_count = 0
                    else:
                        silence_count += 1
                        
                        if silence_count > silence_threshold:
                            # Long silence detected
                            final = json.loads(recognizer.FinalResult())
                            text = final.get('text', '')
                            if text:
                                return text
                            else:
                                return None
                                
            except queue.Empty:
                continue
            except KeyboardInterrupt:
                return None

def main():
    """Main conversation loop"""
    print("=" * 50)
    print("  VOICE CHAT WITH OLLAMA")
    print("=" * 50)
    print(f"Model: {MODEL_NAME}")
    print("Commands:")
    print("  - Speak naturally to chat")
    print("  - Say 'exit' or 'quit' to end")
    print("  - Press Ctrl+C to interrupt")
    print("=" * 50)
    
    speak("Hello! I'm ready to chat. What would you like to talk about?")
    
    while True:
        try:
            # Listen for user input
            user_text = listen()
            
            if user_text is None:
                print("\n⚠️  No speech detected. Try again.")
                continue
            
            print(f"\n👤 You: {user_text}")
            
            # Check for exit commands
            if user_text.lower() in ['exit', 'quit', 'goodbye', 'bye']:
                speak("Goodbye! Have a great day!")
                break
            
            # Get response from Ollama
            response = get_ollama_response(user_text)
            
            # Speak the response
            speak(response)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            speak("Chat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
```

### Step 4: Make Script Executable

```bash
chmod +x voice_chat.py
```

---

## Part 5: Configure the Script

Before running, you may need to adjust settings in the script.

### Option 1: Edit Model Name

If you're using a different model (not phi), edit line 17:

```bash
nano voice_chat.py
```

Change:
```python
MODEL_NAME = "phi"  # Change to: llama2, mistral, tinyllama, etc.
```

### Option 2: Adjust Vosk Model Path

If you downloaded a different Vosk model, update line 18:

```python
VOSK_MODEL_PATH = "/root/vosk-models/YOUR-MODEL-NAME"
```

### Option 3: Adjust Speech Speed

Edit line 24 to make speech faster or slower:

```python
engine.setProperty('rate', 150)  # Try: 120 (slower) to 200 (faster)
```

---

## Part 6: Running the Voice Interface

### Step 1: Ensure Ollama is Running

In one terminal (or background):
```bash
proot-distro login ubuntu
ollama serve &
```

### Step 2: Run the Voice Chat Script

```bash
cd ~/ollama-voice
python3 voice_chat.py
```

### Step 3: Start Talking!

1. Wait for the "Listening..." message
2. Speak your question clearly
3. Pause for 2-3 seconds when done
4. Wait for the response

**Example conversation:**
- You: "What is the capital of France?"
- AI: "The capital of France is Paris..."

---

## Usage Tips

### Getting Better Recognition

1. **Speak clearly** and at a moderate pace
2. **Reduce background noise** (quiet environment works best)
3. **Use a wired headset** for better microphone quality
4. **Pause between questions** to signal you're done speaking

### Controlling the Conversation

- Say **"exit"** or **"quit"** to end the session
- Press **Ctrl+C** to force quit
- The script detects silence to know when you're done speaking

### Improving TTS Quality

The default eSpeak voice is robotic. For better quality, you can:

1. Adjust speech rate (in the script):
   ```python
   engine.setProperty('rate', 140)  # Experiment with values
   ```

2. Try different eSpeak voices:
   ```bash
   espeak --voices
   ```

---

## Part 7: Alternative - Simpler Voice Loop

If the full script is too complex, here's a minimal version:

### Create `simple_voice.py`:

```python
#!/usr/bin/env python3
import subprocess
import requests
import json

MODEL = "phi"
OLLAMA_URL = "http://localhost:11434/api/generate"

def speak(text):
    """Use espeak directly"""
    subprocess.run(["espeak", text])

def ask_ollama(prompt):
    """Get response from Ollama"""
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })
    return response.json()['response']

print("Type your questions (or 'quit' to exit):")
while True:
    user_input = input("\nYou: ")
    if user_input.lower() in ['quit', 'exit']:
        speak("Goodbye!")
        break
    
    print("Thinking...")
    response = ask_ollama(user_input)
    print(f"AI: {response}")
    speak(response)
```

**Usage:**
```bash
python3 simple_voice.py
```

This version requires **typing** input but **speaks** the output - good for testing TTS.

---

## Troubleshooting

### No Audio Output

**Problem:** Script runs but no sound
**Solutions:**
1. Test eSpeak: `espeak "test"`
2. Check phone volume
3. Try: `apt install espeak-ng` (newer version)
4. Check Termux audio permissions in Android settings

### "Cannot connect to Ollama"

**Problem:** Connection refused error
**Solutions:**
1. Check Ollama is running: `ps aux | grep ollama`
2. Start it: `ollama serve &`
3. Test manually: `curl http://localhost:11434/api/generate -d '{"model":"phi","prompt":"hi","stream":false}'`

### "No speech detected"

**Problem:** Voice input not working
**Solutions:**
1. Check microphone permissions for Termux
2. Test recording: `arecord -d 3 test.wav` (if available)
3. Speak louder and more clearly
4. Download larger Vosk model for better accuracy

### High CPU Usage

**Problem:** Phone gets hot/slow
**Solutions:**
1. Use smaller models (tinyllama instead of llama2)
2. Close other apps
3. Lower speech recognition sample rate (in script)
4. Don't run while charging

### Import Errors

**Problem:** "ModuleNotFoundError"
**Solutions:**
```bash
pip3 install pyttsx3 vosk sounddevice numpy requests
```

### Vosk Model Not Found

**Problem:** "Error loading Vosk model"
**Solutions:**
1. Check path: `ls ~/vosk-models/`
2. Re-download model
3. Update `VOSK_MODEL_PATH` in script to match actual folder name

---

## Advanced Customization

### Using Better Vosk Models

Download larger models for improved accuracy:

```bash
cd ~/vosk-models

# Medium model (~128MB)
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip
unzip vosk-model-en-us-0.22-lgraph.zip

# Large model (~1.8GB) - best accuracy
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip
```

Update the script to use the new model path.

### Adding Conversation History

To give the AI memory of your conversation, modify the script to maintain a history:

```python
# Add at top of script
conversation_history = []

# Modify get_ollama_response function
def get_ollama_response(prompt):
    conversation_history.append(f"User: {prompt}")
    full_prompt = "\n".join(conversation_history) + "\nAssistant:"
    
    # ... rest of function
    
    conversation_history.append(f"Assistant: {response}")
    return response
```

### Creating a Systemd Service

To auto-start the voice assistant:

```bash
# Create service file
nano ~/.config/systemd/user/ollama-voice.service
```

Add:
```ini
[Unit]
Description=Ollama Voice Assistant

[Service]
ExecStart=/usr/bin/python3 /root/ollama-voice/voice_chat.py
Restart=always

[Install]
WantedBy=default.target
```

Enable:
```bash
systemctl --user enable ollama-voice
systemctl --user start ollama-voice
```

---

## Performance Optimization

### For Low-RAM Devices

1. Use `tinyllama` model (smallest)
2. Use smallest Vosk model (vosk-model-small-en-us-0.15)
3. Reduce sample rate to 8000 in script
4. Close all other apps

### For Better Quality

1. Use larger Ollama models (mistral, llama2)
2. Use larger Vosk models (0.22 or 0.22-lgraph)
3. Use wired headset with good microphone
4. Keep sample rate at 16000

---

## Additional Resources

- **Vosk Models**: https://alphacephei.com/vosk/models
- **pyttsx3 Documentation**: https://pyttsx3.readthedocs.io/
- **Ollama API Docs**: https://github.com/ollama/ollama/blob/main/docs/api.md
- **Termux Wiki**: https://wiki.termux.com/wiki/Main_Page

---

## Security & Privacy

✅ **Completely Offline**: Both speech recognition (Vosk) and AI (Ollama) run locally
✅ **No Cloud Services**: Your voice and conversations never leave your device
✅ **Private**: No data collection or external API calls
✅ **Open Source**: All tools used are open source and auditable

---

**Congratulations!** You now have a fully voice-enabled AI assistant running completely locally on your Android device. Enjoy hands-free conversations with complete privacy!