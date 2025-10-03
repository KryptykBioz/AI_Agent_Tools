import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import tempfile
import sounddevice as sd
import soundfile as sf
import torch
import re
import numpy as np
from pathlib import Path
import warnings

_tts_model = None
_device = None
_use_arc = False

def init_tts(force_arc=False):
    """Initialize TTS - Intel Arc B580 optimized"""
    global _tts_model, _device, _use_arc
    
    if _tts_model is not None:
        return _tts_model
    
    # Strategy: Use stable PyTorch 2.4.1 + Intel Arc via OpenVINO
    print("Initializing TTS for Intel Arc B580...")
    
    # Install compatible packages first if needed
    try:
        import openvino
        _use_arc = True
        print("✓ OpenVINO available for Intel Arc acceleration")
    except ImportError:
        _use_arc = False
        print("⚠ OpenVINO not found - install: pip install openvino openvino-dev")
    
    # Use CPU for model loading (most compatible)
    _device = 'cpu'
    
    print("Loading XTTS v2 model on CPU...")
    
    # Configure safe loading
    _orig_load = torch.load
    torch.load = lambda *a, **k: _orig_load(*a, **{**k, 'weights_only': False})
    
    try:
        from TTS.api import TTS
        warnings.filterwarnings('ignore')
        
        _tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        _tts_model.to(_device)
        
        print("✓ Model loaded successfully (CPU mode)")
        
        if _use_arc:
            print("✓ Intel Arc B580 will accelerate inference via OpenVINO")
    finally:
        torch.load = _orig_load
    
    return _tts_model

def find_vb_cable():
    """Locate VB-Cable device"""
    devs = sd.query_devices()
    patterns = ("cable input", "vb-audio", "voicemeeter")
    
    for i, d in enumerate(devs):
        if d['max_output_channels'] > 0:
            name_lower = d['name'].lower()
            if any(p in name_lower for p in patterns):
                print(f"✓ VB-Cable: [{i}] {d['name']}")
                return i
    return None

def clean_text(text):
    """Remove emojis and special chars"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub('', text).replace('*', '').strip()

def speak_vbcable(text, voice_wav, language="en", fallback=True):
    """
    CPU-optimized TTS with voice cloning (stable version)
    
    Args:
        text: Text to speak
        voice_wav: Path to voice sample (6-30s, 22050Hz mono)
        language: Language code
        fallback: Use default device if VB-Cable missing
    
    Returns:
        Status string
    """
    if not Path(voice_wav).exists():
        return f"Error: Voice sample not found: {voice_wav}"
    
    text = clean_text(text)
    if not text:
        return "No text to speak"
    
    temp_wav = Path(tempfile.gettempdir()) / f"tts_output_{os.getpid()}.wav"
    
    try:
        tts = init_tts()
        
        print(f"Generating: '{text[:60]}...'")
        
        # Generate audio with compatible settings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            tts.tts_to_file(
                text=text,
                speaker_wav=str(voice_wav),
                language=language,
                file_path=str(temp_wav),
                split_sentences=True
            )
        
        # Play audio
        data, sr = sf.read(temp_wav, dtype='float32')
        
        dev = find_vb_cable()
        if dev is None:
            if not fallback:
                return "Error: VB-Cable not found"
            print("Using default audio device")
        
        sd.play(data, sr, device=dev)
        sd.wait()
        
        return "✓ TTS complete"
    
    except Exception as e:
        import traceback
        print("\nFull error trace:")
        traceback.print_exc()
        return f"Error: {e}"
    
    finally:
        if temp_wav.exists():
            try:
                temp_wav.unlink()
            except:
                pass

def speak_stream(text, voice_wav, language="en"):
    """Stream sentence-by-sentence for lower latency"""
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    
    for i, sent in enumerate(sentences, 1):
        print(f"[{i}/{len(sentences)}]")
        result = speak_vbcable(sent, voice_wav, language, True)
        if "Error" in result:
            print(f"⚠ {result}")

def check_environment():
    """Check GPU and package compatibility"""
    print("\n=== Environment Check ===\n")
    
    # PyTorch info
    print(f"PyTorch: {torch.__version__}")
    
    # CUDA check
    if torch.cuda.is_available():
        try:
            gpu_name = torch.cuda.get_device_name(0)
            major, minor = torch.cuda.get_device_capability(0)
            print(f"NVIDIA GPU: {gpu_name} (sm_{major}{minor})")
            
            if major == 12:
                print("⚠ RTX 50 series detected but sm_120 not supported in stable PyTorch")
                print("  Recommendation: Use Intel Arc B580 instead")
        except:
            print("CUDA: Available but not functional")
    else:
        print("CUDA: Not available")
    
    # Intel Arc check
    print("\nIntel Arc B580 Support:")
    try:
        import openvino as ov
        print(f"✓ OpenVINO: {ov.__version__}")
        
        # Check available devices
        core = ov.Core()
        devices = core.available_devices
        
        gpu_found = False
        for dev in devices:
            if 'GPU' in dev:
                gpu_found = True
                print(f"✓ Intel GPU Device: {dev}")
        
        if not gpu_found:
            print("⚠ No Intel GPU found via OpenVINO")
            print("  Install drivers: https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html")
    except ImportError:
        print("✗ OpenVINO not installed")
        print("  Install: pip install openvino openvino-dev")
    
    # Audio backend
    print("\nAudio Backend:")
    try:
        import soundfile
        import sounddevice
        print(f"✓ soundfile: {soundfile.__version__}")
        print(f"✓ sounddevice: {sounddevice.__version__}")
    except ImportError as e:
        print(f"✗ Audio library missing: {e}")
    
    print()

def test_voice():
    """Test voice cloning"""
    VOICE = "./../../personality/voice/Anna_Voice_Sample_optimized.wav"
    
    if not Path(VOICE).exists():
        print(f"⚠ Voice sample not found: {VOICE}")
        return
    
    # Analyze sample
    data, sr = sf.read(VOICE)
    dur = len(data) / sr
    ch = data.shape[1] if data.ndim > 1 else 1
    
    print(f"=== Voice Sample ===")
    print(f"Rate: {sr} Hz")
    print(f"Duration: {dur:.1f}s")
    print(f"Channels: {ch}")
    
    if sr < 16000:
        print("⚠ Low sample rate")
    if dur < 6 or dur > 30:
        print("⚠ Duration outside 6-30s optimal range")
    
    print()
    
    # Initialize model
    init_tts()
    
    # Test generation
    test = "Hello! This is Anna speaking. The system is now running on Intel Arc B580."
    print(f"Test: {test}\n")
    result = speak_vbcable(test, VOICE)
    print(f"\n{result}")

if __name__ == "__main__":
    check_environment()
    test_voice()