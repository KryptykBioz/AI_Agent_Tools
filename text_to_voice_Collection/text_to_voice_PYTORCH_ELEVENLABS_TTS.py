# Force CPU mode - must be before any torch imports
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

import tempfile
import sounddevice as sd
import soundfile as sf
from TTS.api import TTS
import re

# Global model cache for performance
_tts_model = None
_device = None

def init_tts(use_gpu=True):
    """Initialize TTS model once (expensive operation)"""
    global _tts_model, _device
    
    if _tts_model is None:
        import torch
        
        # Register all TTS classes as safe globals for PyTorch 2.6+
        try:
            from TTS.tts.configs.xtts_config import XttsConfig
            from TTS.tts.models.xtts import XttsAudioConfig
            torch.serialization.add_safe_globals([XttsConfig, XttsAudioConfig])
        except ImportError:
            pass
        
        # Alternative: Use weights_only=False (less secure but works)
        import torch.serialization
        original_load = torch.load
        torch.load = lambda *args, **kwargs: original_load(*args, **{**kwargs, 'weights_only': False})
        
        # Check if GPU is actually usable
        gpu_available = use_gpu and torch.cuda.is_available()
        if gpu_available:
            try:
                # Test if GPU actually works
                torch.zeros(1).cuda()
                _device = "cuda"
                print(f"Loading XTTS v2 model on {_device}...")
            except RuntimeError as e:
                if "no kernel image" in str(e):
                    print(f"⚠ GPU detected but not compatible with PyTorch (sm_120 not supported)")
                    print("⚠ Falling back to CPU mode")
                    _device = "cpu"
                else:
                    raise
        else:
            _device = "cpu"
            print(f"Loading XTTS v2 model on {_device}...")
        
        _tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(_device)
        print("Model loaded successfully")
        
        # Restore original torch.load
        torch.load = original_load
    
    return _tts_model

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
        if device['max_output_channels'] > 0:
            for pattern in cable_patterns:
                if pattern.lower() in device_name.lower():
                    print(f"Found VB-Cable: [{i}] {device_name}")
                    return i
    return None

def remove_emoji(text):
    """Remove emoji characters from text"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def speak_through_vbcable(text, voice_sample_path, language="en", use_fallback=True, use_gpu=True):
    """
    Speak text through VB-Cable using voice cloning (100% local)
    
    Args:
        text: Text to speak
        voice_sample_path: Path to ElevenLabs voice sample (wav/mp3)
        language: Language code (en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, ko, hu)
        use_fallback: Fall back to default audio device if VB-Cable not found
        use_gpu: Use GPU acceleration if available
    
    Returns:
        Status message string
    """
    temp_wav = os.path.join(tempfile.gettempdir(), "tts_cloned_output.wav")
    
    try:
        # Verify voice sample exists
        if not os.path.exists(voice_sample_path):
            raise FileNotFoundError(f"Voice sample not found: {voice_sample_path}")
        
        # Initialize model
        tts = init_tts(use_gpu)
        
        # Clean text
        text_clean = remove_emoji(text).replace('*', '').strip()
        
        if not text_clean:
            return "No text to speak"
        
        # Generate speech with voice cloning
        print(f"Generating speech: '{text_clean[:50]}...'")
        tts.tts_to_file(
            text=text_clean,
            speaker_wav=voice_sample_path,
            language=language,
            file_path=temp_wav
        )
        
        # Find output device
        cable_index = find_vb_cable_device()
        if cable_index is None and not use_fallback:
            raise RuntimeError("VB-Cable not found and fallback disabled")
        
        # Load and play audio
        data, samplerate = sf.read(temp_wav, dtype='float32')
        
        if cable_index is not None:
            sd.play(data, samplerate, device=cable_index)
            print(f"Playing through VB-Cable device [{cable_index}]")
        else:
            sd.play(data, samplerate)
            print("Playing through default audio device")
        
        sd.wait()
        return "TTS executed successfully"
    
    except Exception as e:
        print(f"TTS Error: {e}")
        return f"TTS failed: {e}"
    
    finally:
        # Cleanup
        if os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception as e:
                print(f"Could not remove temp file: {e}")

def speak_through_vbcable_stream(text, voice_sample_path, language="en", use_gpu=True):
    """
    Stream TTS output sentence-by-sentence for lower latency
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for i, sentence in enumerate(sentences):
        if sentence.strip():
            print(f"Speaking sentence {i+1}/{len(sentences)}")
            speak_through_vbcable(sentence.strip(), voice_sample_path, language, True, use_gpu)

def test_voice_cloning(voice_sample_path):
    """Test voice cloning setup"""
    print("\n=== Voice Cloning Test ===")
    
    # Check voice sample
    if not os.path.exists(voice_sample_path):
        print(f"❌ Voice sample not found: {voice_sample_path}")
        print("Please provide path to your ElevenLabs voice sample (.wav or .mp3)")
        return False
    
    print(f"✓ Voice sample found: {voice_sample_path}")
    
    # Check GPU
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ GPU available: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠ No GPU found, using CPU (slower)")
    except:
        print("⚠ PyTorch not configured for GPU")
    
    # Check VB-Cable
    cable_idx = find_vb_cable_device()
    if cable_idx is not None:
        print(f"✓ VB-Cable found at device index {cable_idx}")
    else:
        print("⚠ VB-Cable not found (will use default audio device)")
    
    # Test TTS
    print("\nLoading model and testing voice cloning...")
    test_text = "Hello! This is a test of the voice cloning system using your ElevenLabs voice sample. My name is Anna. It's nice to meet you."
    result = speak_through_vbcable(test_text, voice_sample_path, use_gpu=True)
    print(f"\n{result}")
    
    print("\n=== Test Complete ===")
    return True

# Add this to the bottom of text_to_voice.py and run it
if __name__ == "__main__":
    import soundfile as sf
    
    VOICE_SAMPLE = "./../../personality/voice/Anna_Voice_Sample_optimized.wav"
    
    # Analyze the sample
    data, sr = sf.read(VOICE_SAMPLE)
    duration = len(data) / sr
    
    print(f"\n=== Voice Sample Analysis ===")
    print(f"Sample rate: {sr} Hz")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Channels: {data.shape[1] if len(data.shape) > 1 else 1}")
    print(f"Ideal: 22050-24000 Hz, 6-30 seconds, mono")
    
    if sr < 16000:
        print("⚠ WARNING: Sample rate too low - may cause quality issues")
    if duration < 3:
        print("⚠ WARNING: Sample too short - needs 6-30 seconds for best results")
    if duration > 30:
        print("⚠ WARNING: Sample too long - trim to 10-15 seconds")
    
    # Now run the actual test
    test_voice_cloning(VOICE_SAMPLE)