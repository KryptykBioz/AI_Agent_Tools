# tts_vbcable.py - Improved version with better device detection and fallback

import os
import tempfile
import pyttsx3
import sounddevice as sd
import soundfile as sf
from personality.bot_info import voiceIndex
import re

def list_audio_devices():
    """List all available audio devices for debugging"""
    devices = sd.query_devices()
    print("\n=== Available Audio Devices ===")
    for i, device in enumerate(devices):
        device_info = f"[{i}] {device['name']}"
        if device['max_output_channels'] > 0:
            device_info += " (Output)"
        if device['max_input_channels'] > 0:
            device_info += " (Input)"
        print(device_info)
    print("===============================\n")
    return devices

def find_vb_cable_device():
    """Find VB-Cable device with multiple search patterns"""
    devices = sd.query_devices()
    cable_patterns = [
        "CABLE Input",
        "VB-Audio Virtual Cable",
        "Virtual Cable",
        "CABLE-A Input",
        "CABLE-B Input",
        "VoiceMeeter Input",
        "VoiceMeeter Aux Input"
    ]
    
    for i, device in enumerate(devices):
        device_name = device['name']
        # Only consider output devices
        if device['max_output_channels'] > 0:
            for pattern in cable_patterns:
                if pattern.lower() in device_name.lower():
                    print(f"Found VB-Cable device: [{i}] {device_name}")
                    return i
    
    return None

def remove_emoji(text: str) -> str:
    """Remove emoji characters from text"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def speak_through_vbcable(text, use_fallback=True):
    """
    Speak text through VB-Cable with fallback options
    
    Args:
        text: Text to speak
        use_fallback: If True, fall back to default audio device if VB-Cable not found
    """
    # Set up pyttsx3 with desired voice settings
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    # Ensure voiceIndex is valid
    if voiceIndex < len(voices):
        engine.setProperty('voice', voices[voiceIndex].id)
    else:
        print(f"Warning: voiceIndex {voiceIndex} out of range, using default voice")
    
    engine.setProperty('rate', 200)
    engine.setProperty('volume', 1.0)

    # Generate speech and save to a temporary WAV file
    temp_wav = os.path.join(tempfile.gettempdir(), "tts_output.wav")
    text = remove_emoji(text)
    text = text.replace('*', '')
    engine.save_to_file(text, temp_wav)
    engine.runAndWait()

    try:
        # Try to find VB-Cable device
        cable_index = find_vb_cable_device()
        
        if cable_index is None:
            if use_fallback:
                print("VB-Cable device not found, using default audio device")
                cable_index = None  # Use default device
            else:
                # List available devices for debugging
                list_audio_devices()
                raise RuntimeError("VB-Cable device not found! Please install VB-Cable or check device names above.")

        # Load and play the audio
        data, samplerate = sf.read(temp_wav, dtype='float32')
        
        if cable_index is not None:
            sd.play(data, samplerate, device=cable_index)
            print(f"Playing audio through device [{cable_index}]")
        else:
            sd.play(data, samplerate)  # Use default device
            print("Playing audio through default device")
            
        sd.wait()

        return "TTS executed successfully."

    except Exception as e:
        if use_fallback:
            print(f"Audio playback failed ({e}), trying pyttsx3 direct output...")
            # Fallback to direct pyttsx3 output
            try:
                engine.say(text)
                engine.runAndWait()
                return "TTS executed via pyttsx3 fallback."
            except Exception as e2:
                return f"All TTS methods failed: {e2}"
        else:
            raise e
    
    finally:
        # Clean up temp file
        try:
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
        except Exception as e:
            print(f"Warning: Could not remove temp file {temp_wav}: {e}")

def test_audio_setup():
    """Test function to diagnose audio setup"""
    print("=== Audio Setup Diagnosis ===")
    
    # List all devices
    devices = list_audio_devices()
    
    # Try to find VB-Cable
    cable_index = find_vb_cable_device()
    
    if cable_index is not None:
        print(f"✓ VB-Cable found at index {cable_index}")
    else:
        print("✗ VB-Cable not found")
        print("\nTo fix this:")
        print("1. Install VB-Cable from: https://vb-audio.com/Cable/")
        print("2. Or install VoiceMeeter which includes virtual cables")
        print("3. Restart your application after installation")
    
    # Test pyttsx3
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print(f"\n✓ pyttsx3 initialized with {len(voices)} voices available")
        
        from personality.bot_info import voiceIndex
        if voiceIndex < len(voices):
            print(f"✓ Voice index {voiceIndex} is valid: {voices[voiceIndex].name}")
        else:
            print(f"✗ Voice index {voiceIndex} is out of range (max: {len(voices)-1})")
            
    except Exception as e:
        print(f"✗ pyttsx3 error: {e}")
    
    return cable_index is not None

# Example usage
if __name__ == "__main__":
    # Run diagnosis
    test_audio_setup()
    
    # Test TTS
    test_text = "This is a test of the improved VB-Cable text to speech system with fallback support."
    print(f"\nTesting TTS with: '{test_text}'")
    result = speak_through_vbcable(test_text)
    print(f"Result: {result}")