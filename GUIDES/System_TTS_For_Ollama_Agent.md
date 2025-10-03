# Text-to-Speech Integration Guide for Ollama Agents

This guide will help you implement system text-to-speech (TTS) capabilities for your Ollama agent, allowing it to read responses aloud through your system's audio devices or virtual audio cables.

## Prerequisites

### Required Python Libraries

Install the following packages using pip:

```bash
pip install pyttsx3 sounddevice soundfile
```

- **pyttsx3**: Cross-platform text-to-speech library
- **sounddevice**: Audio playback and device management
- **soundfile**: Audio file reading and writing

### Optional: Virtual Audio Cable

For advanced audio routing (e.g., streaming, recording, or audio processing):

1. **VB-Cable** (Windows): Download from [https://vb-audio.com/Cable/](https://vb-audio.com/Cable/)
2. **VoiceMeeter** (Windows): Includes virtual cables - [https://vb-audio.com/Voicemeeter/](https://vb-audio.com/Voicemeeter/)
3. **BlackHole** (macOS): Virtual audio driver for Mac
4. **PulseAudio** (Linux): Built-in virtual audio support

## Implementation

### Basic TTS Function

Create a Python module for text-to-speech functionality:

```python
import os
import tempfile
import pyttsx3
import sounddevice as sd
import soundfile as sf
import re

def remove_emoji(text: str) -> str:
    """Remove emoji characters from text"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def speak_text(text, voice_index=0, rate=200, volume=1.0):
    """
    Convert text to speech and play through default audio device
    
    Args:
        text: Text to speak
        voice_index: Index of voice to use (0 = default)
        rate: Speech rate (words per minute)
        volume: Volume level (0.0 to 1.0)
    """
    # Initialize TTS engine
    engine = pyttsx3.init()
    
    # Configure voice settings
    voices = engine.getProperty('voices')
    if voice_index < len(voices):
        engine.setProperty('voice', voices[voice_index].id)
    
    engine.setProperty('rate', rate)
    engine.setProperty('volume', volume)
    
    # Clean text
    text = remove_emoji(text)
    text = text.replace('*', '')  # Remove markdown asterisks
    
    # Generate and save audio
    temp_wav = os.path.join(tempfile.gettempdir(), "tts_output.wav")
    engine.save_to_file(text, temp_wav)
    engine.runAndWait()
    
    try:
        # Load and play audio
        data, samplerate = sf.read(temp_wav, dtype='float32')
        sd.play(data, samplerate)
        sd.wait()
        return "Speech completed successfully"
    except Exception as e:
        # Fallback to direct pyttsx3 output
        engine.say(text)
        engine.runAndWait()
        return f"Speech completed via fallback: {e}"
    finally:
        # Cleanup
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
```

### Advanced: Virtual Audio Cable Support

For routing audio through virtual cables:

```python
def list_audio_devices():
    """List all available audio output devices"""
    devices = sd.query_devices()
    print("\n=== Available Audio Devices ===")
    for i, device in enumerate(devices):
        if device['max_output_channels'] > 0:
            print(f"[{i}] {device['name']} (Output)")
    print("================================\n")
    return devices

def find_virtual_cable():
    """Find virtual audio cable device"""
    devices = sd.query_devices()
    
    # Common virtual cable names
    patterns = [
        "CABLE Input",
        "VB-Audio Virtual Cable",
        "Virtual Cable",
        "VoiceMeeter Input",
        "BlackHole"
    ]
    
    for i, device in enumerate(devices):
        if device['max_output_channels'] > 0:
            for pattern in patterns:
                if pattern.lower() in device['name'].lower():
                    print(f"Found virtual cable: [{i}] {device['name']}")
                    return i
    return None

def speak_to_device(text, device_index=None, voice_index=0):
    """
    Speak through a specific audio device
    
    Args:
        text: Text to speak
        device_index: Audio device index (None = default)
        voice_index: Voice index to use
    """
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    if voice_index < len(voices):
        engine.setProperty('voice', voices[voice_index].id)
    
    engine.setProperty('rate', 200)
    engine.setProperty('volume', 1.0)
    
    # Clean and prepare text
    text = remove_emoji(text)
    text = text.replace('*', '')
    
    temp_wav = os.path.join(tempfile.gettempdir(), "tts_output.wav")
    engine.save_to_file(text, temp_wav)
    engine.runAndWait()
    
    try:
        data, samplerate = sf.read(temp_wav, dtype='float32')
        
        if device_index is not None:
            sd.play(data, samplerate, device=device_index)
            print(f"Playing through device [{device_index}]")
        else:
            sd.play(data, samplerate)
            print("Playing through default device")
        
        sd.wait()
        return "Success"
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
```

## Integration with Ollama Agent

### Method 1: Post-Processing Response

```python
import ollama

def chat_with_tts(message, model="llama2"):
    """Send message to Ollama and speak the response"""
    response = ollama.chat(model=model, messages=[
        {'role': 'user', 'content': message}
    ])
    
    reply = response['message']['content']
    print(f"Agent: {reply}")
    
    # Speak the response
    speak_text(reply)
    
    return reply
```

### Method 2: Streaming with TTS

```python
def chat_with_streaming_tts(message, model="llama2"):
    """Stream Ollama response and speak complete sentences"""
    buffer = ""
    
    stream = ollama.chat(
        model=model,
        messages=[{'role': 'user', 'content': message}],
        stream=True
    )
    
    for chunk in stream:
        content = chunk['message']['content']
        buffer += content
        print(content, end='', flush=True)
        
        # Speak when we have complete sentences
        if any(punct in content for punct in ['.', '!', '?']):
            speak_text(buffer.strip())
            buffer = ""
    
    # Speak any remaining text
    if buffer.strip():
        speak_text(buffer.strip())
```

## Voice Configuration

### Listing Available Voices

```python
def list_available_voices():
    """Display all system TTS voices"""
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    print("\n=== Available Voices ===")
    for i, voice in enumerate(voices):
        print(f"[{i}] {voice.name}")
        print(f"    ID: {voice.id}")
        print(f"    Languages: {voice.languages}")
        print()
```

### Testing Voice Settings

```python
def test_voice_settings():
    """Test different voice configurations"""
    test_text = "This is a test of the text to speech system."
    
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    print(f"Testing {len(voices)} available voices...\n")
    
    for i, voice in enumerate(voices):
        print(f"Voice {i}: {voice.name}")
        engine.setProperty('voice', voice.id)
        engine.say(test_text)
        engine.runAndWait()
```

## Diagnostic Tools

### Audio Setup Diagnosis

```python
def diagnose_audio_setup():
    """Check audio configuration and capabilities"""
    print("=== Audio Setup Diagnosis ===\n")
    
    # Check available devices
    list_audio_devices()
    
    # Check for virtual cables
    cable = find_virtual_cable()
    if cable:
        print(f"✓ Virtual cable found at index {cable}")
    else:
        print("✗ No virtual cable detected")
    
    # Check TTS engine
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print(f"\n✓ TTS engine initialized")
        print(f"✓ {len(voices)} voices available")
    except Exception as e:
        print(f"✗ TTS engine error: {e}")
```

## Usage Examples

### Basic Usage

```python
# Simple TTS
speak_text("Hello, I am your Ollama agent assistant.")

# With custom voice
speak_text("This uses a different voice.", voice_index=1)

# Adjust speed
speak_text("Speaking faster now!", rate=250)
```

### With Ollama Integration

```python
# Setup
import ollama

# Chat with voice output
user_input = "What is machine learning?"
response = chat_with_tts(user_input, model="llama2")

# Use specific audio device
device_id = find_virtual_cable()
if device_id:
    speak_to_device(response, device_index=device_id)
```

## Troubleshooting

### Common Issues

**No audio output:**
- Run `diagnose_audio_setup()` to check device configuration
- Verify audio drivers are installed and up to date
- Check system volume settings

**Wrong audio device:**
- Use `list_audio_devices()` to see all devices
- Specify device index explicitly in `speak_to_device()`

**Robotic or poor quality voice:**
- Try different voice indices using `list_available_voices()`
- Install additional TTS voices from your OS settings
- Adjust the rate parameter (150-250 is typical)

**Text not cleaning properly:**
- Extend the `remove_emoji()` function for additional characters
- Add custom text preprocessing for your use case

## Best Practices

1. **Always clean text** before speaking (remove emojis, markdown, special characters)
2. **Handle errors gracefully** with fallback methods
3. **Test voice settings** before deployment
4. **Consider sentence-level TTS** for streaming responses
5. **Cleanup temporary files** to avoid disk space issues
6. **Adjust rate and volume** based on voice characteristics
7. **Use virtual cables** for advanced audio routing needs

## Platform-Specific Notes

- **Windows**: Best support with native SAPI5 voices and VB-Cable
- **macOS**: Use `nsss` backend, consider BlackHole for virtual audio
- **Linux**: May require `espeak` or `festival` installation, use PulseAudio for routing

## Conclusion

This guide provides a complete foundation for adding TTS capabilities to your Ollama agent, allowing it to speak responses through your system audio or virtual audio devices.