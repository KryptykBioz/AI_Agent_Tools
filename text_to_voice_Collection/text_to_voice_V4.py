import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '8'
os.environ['MKL_NUM_THREADS'] = '8'

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
_voice_cache = {}

def init_tts():
    """Initialize TTS with CPU optimizations"""
    global _tts_model, _device
    
    if _tts_model is not None:
        return _tts_model
    
    _device = 'cpu'
    
    # CPU optimizations
    torch.set_num_threads(8)
    torch.set_num_interop_threads(4)
    
    print("Loading XTTS v2 (optimized)...")
    
    _orig_load = torch.load
    torch.load = lambda *a, **k: _orig_load(*a, **{**k, 'weights_only': False})
    
    try:
        from TTS.api import TTS
        warnings.filterwarnings('ignore')
        
        _tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        _tts_model.to(_device)
        
        # Optimize for inference
        if hasattr(_tts_model, 'synthesizer') and hasattr(_tts_model.synthesizer, 'tts_model'):
            model = _tts_model.synthesizer.tts_model
            model.eval()
            for param in model.parameters():
                param.requires_grad = False
        
        print("✓ Model loaded")
    finally:
        torch.load = _orig_load
    
    return _tts_model

def cache_voice_embeddings(voice_wav):
    """Pre-compute voice embeddings for speed"""
    global _voice_cache
    
    voice_key = str(voice_wav)
    if voice_key in _voice_cache:
        return _voice_cache[voice_key]
    
    tts = init_tts()
    model = tts.synthesizer.tts_model
    
    print("Computing voice embeddings...")
    
    with torch.no_grad():
        gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
            audio_path=str(voice_wav)
        )
    
    _voice_cache[voice_key] = (gpt_cond_latent, speaker_embedding)
    print("✓ Embeddings cached")
    
    return gpt_cond_latent, speaker_embedding

def find_vb_cable():
    """Locate VB-Cable"""
    devs = sd.query_devices()
    patterns = ("cable input", "vb-audio", "voicemeeter")
    
    for i, d in enumerate(devs):
        if d['max_output_channels'] > 0:
            if any(p in d['name'].lower() for p in patterns):
                return i
    return None

def clean_text(text):
    """Remove emojis"""
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

def speak_vbcable(text, voice_wav, language="en", fallback=True, use_cache=True):
    """
    Optimized TTS with voice cloning
    
    Args:
        text: Text to speak
        voice_wav: Path to voice sample
        language: Language code
        fallback: Use default device if no VB-Cable
        use_cache: Cache voice embeddings (faster)
    """
    if not Path(voice_wav).exists():
        return f"Error: Voice sample not found"
    
    text = clean_text(text)
    if not text:
        return "No text"
    
    temp_wav = Path(tempfile.gettempdir()) / f"tts_{os.getpid()}.wav"
    
    try:
        tts = init_tts()
        model = tts.synthesizer.tts_model
        
        print(f"Generating: '{text[:60]}...'")
        
        with torch.no_grad():
            if use_cache:
                # Fast: Use cached embeddings
                gpt_cond_latent, speaker_embedding = cache_voice_embeddings(voice_wav)
                
                out = model.inference(
                    text=text,
                    language=language,
                    gpt_cond_latent=gpt_cond_latent,
                    speaker_embedding=speaker_embedding,
                    temperature=0.7,
                    length_penalty=1.0,
                    repetition_penalty=5.0,
                    top_k=50,
                    top_p=0.85,
                    speed=1.0,
                    enable_text_splitting=True
                )
                wav = out['wav']
            else:
                # Slow: Compute embeddings each time
                out = model.synthesize(
                    text=text,
                    config=model.config,
                    speaker_wav=str(voice_wav),
                    language=language,
                    temperature=0.7,
                    length_penalty=1.0,
                    repetition_penalty=5.0,
                    top_k=50,
                    top_p=0.85,
                    speed=1.0,
                    enable_text_splitting=True
                )
                wav = out['wav']
        
        # Convert and normalize
        if isinstance(wav, torch.Tensor):
            wav = wav.cpu().numpy()
        
        wav = np.clip(wav, -1.0, 1.0)
        sf.write(temp_wav, wav, 24000)
        
        # Play
        data, sr = sf.read(temp_wav, dtype='float32')
        
        dev = find_vb_cable()
        if dev is None and not fallback:
            return "Error: No VB-Cable"
        
        sd.play(data, sr, device=dev)
        sd.wait()
        
        return "✓ Complete"
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {e}"
    
    finally:
        if temp_wav.exists():
            try:
                temp_wav.unlink()
            except:
                pass

def speak_stream(text, voice_wav, language="en"):
    """Stream sentences with cached embeddings"""
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    
    # Cache once
    cache_voice_embeddings(voice_wav)
    
    for i, sent in enumerate(sentences, 1):
        print(f"[{i}/{len(sentences)}]")
        speak_vbcable(sent, voice_wav, language, True, True)

def benchmark():
    """Performance benchmark"""
    import time
    
    VOICE = "./../../personality/voice/Anna_Voice_Sample_optimized.wav"
    
    if not Path(VOICE).exists():
        print(f"⚠ Voice not found")
        return
    
    print("\n=== Benchmark ===\n")
    
    init_tts()
    
    test = "The quick brown fox jumps over the lazy dog."
    
    # Without cache
    print("Test 1: Cold start")
    start = time.perf_counter()
    speak_vbcable(test, VOICE, use_cache=False)
    t1 = time.perf_counter() - start
    print(f"Time: {t1:.2f}s\n")
    
    # With cache
    print("Test 2: Cached")
    start = time.perf_counter()
    speak_vbcable(test, VOICE, use_cache=True)
    t2 = time.perf_counter() - start
    print(f"Time: {t2:.2f}s")
    
    if t2 > 0:
        print(f"\nSpeedup: {t1/t2:.1f}x")
        print(f"RTF: {t2/(len(test.split())*0.3):.2f}x")
    
    print("\n=== Complete ===\n")

def test_voice():
    """Test voice"""
    VOICE = "./../../personality/voice/Anna_Voice_Sample_optimized.wav"
    
    if not Path(VOICE).exists():
        print(f"⚠ Voice not found")
        return
    
    data, sr = sf.read(VOICE)
    dur = len(data) / sr
    
    print(f"=== Voice ===")
    print(f"Rate: {sr} Hz")
    print(f"Duration: {dur:.1f}s\n")
    
    init_tts()
    
    test = "Hello! This is Anna. The system is now optimized."
    print(f"Test: {test}\n")
    speak_vbcable(test, VOICE, use_cache=True)

if __name__ == "__main__":
    benchmark()
    
    print("\n=== Streaming ===\n")
    VOICE = "./../../personality/voice/Anna_Voice_Sample_optimized.wav"
    if Path(VOICE).exists():
        text = "Hello! This is streaming mode. Each sentence generates separately. This is much faster."
        speak_stream(text, VOICE)