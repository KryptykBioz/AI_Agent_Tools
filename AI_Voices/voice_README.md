# Voice System Setup

## Overview

Anna AI now features **AI-powered voice cloning** using Coqui XTTS v2, allowing the assistant to speak with a custom voice based on a reference audio sample. This replaces the previous system TTS implementation with a more natural and personalized voice experience.

## Architecture

The voice system consists of three main components:

1. **Voice Cloning Engine** - Coqui TTS XTTS v2 model for neural voice synthesis
2. **Audio Processing** - Voice sample optimization and audio output handling
3. **VB-Cable Integration** - Virtual audio routing for flexible audio management

## Requirements

### Python Version
- **Python 3.11.x** (specifically 3.11.9 recommended)
- ⚠️ **Not compatible** with Python 3.12+ or 3.13 due to Coqui TTS limitations

### Core Dependencies

```bash
# Voice cloning and TTS
TTS==0.22.0                    # Coqui TTS for voice cloning
transformers==4.46.0           # Language models (specific version required)

# Audio processing
sounddevice                    # Audio playback
soundfile                      # Audio file I/O
librosa                        # Audio analysis and processing
numpy                          # Numerical operations

# PyTorch (CPU mode)
torch==2.5.1
torchaudio==2.5.1
```

### Installation

```bash
# 1. Create Python 3.11 virtual environment
py -3.11 -m venv venv
venv\Scripts\activate

# 2. Install core dependencies
pip install --upgrade pip
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124

# 3. Install TTS and compatible transformers
pip install transformers==4.46.0 TTS==0.22.0

# 4. Install audio processing libraries
pip install sounddevice soundfile librosa numpy
```

### Optional: VB-Cable Audio Router

For advanced audio routing (e.g., streaming, recording, or audio monitoring):

1. Download [VB-Cable](https://vb-audio.com/Cable/) or [VoiceMeeter](https://vb-audio.com/Voicemeeter/)
2. Install and restart your computer
3. The system will automatically detect and use VB-Cable when available
4. Falls back to default audio device if not installed

## Voice Sample Preparation

### Requirements for Voice Samples

Your voice reference sample should meet these specifications:

- **Format**: WAV (preferred) or MP3
- **Duration**: 10-15 seconds (ideal), 6-30 seconds (acceptable)
- **Sample Rate**: 22050 Hz (optimal for XTTS)
- **Channels**: Mono
- **Quality**: Clean audio with minimal background noise
- **Content**: Varied speech with natural prosody and intonation

### Optimizing Your Voice Sample

If your sample doesn't meet the specifications, use the provided optimizer:

```bash
python BASE/tools/optimize_voice_sample.py
```

This will:
- Trim silence from beginning and end
- Resample to 22050 Hz
- Extract the optimal 12-second segment
- Normalize audio levels
- Save as `Anna_Voice_Sample_optimized.wav`

### Recommended Voice Sample Sources

1. **ElevenLabs** - Generate high-quality voice samples (10-15 seconds)
2. **Custom Recording** - Record your own voice with a good microphone
3. **Existing Audio** - Use clean audio clips from interviews, podcasts, etc.

## Usage

### Basic Usage

```python
from tools.text_to_voice import speak_through_vbcable

# Path to your voice sample
VOICE_SAMPLE = "./personality/voice/Anna_Voice_Sample_optimized.wav"

# Generate speech
speak_through_vbcable(
    text="Hello! This is Anna speaking.",
    voice_sample_path=VOICE_SAMPLE,
    language="en"
)
```

### Supported Languages

The XTTS v2 model supports multiple languages:
- English (`en`)
- Spanish (`es`)
- French (`fr`)
- German (`de`)
- Italian (`it`)
- Portuguese (`pt`)
- Polish (`pl`)
- Turkish (`tr`)
- Russian (`ru`)
- Dutch (`nl`)
- Czech (`cs`)
- Arabic (`ar`)
- Chinese (`zh-cn`)
- Japanese (`ja`)
- Korean (`ko`)
- Hungarian (`hu`)

### Advanced Options

```python
speak_through_vbcable(
    text="Your text here",
    voice_sample_path=VOICE_SAMPLE,
    language="en",
    use_fallback=True,    # Fall back to default audio if VB-Cable not found
    use_gpu=False         # Set to True if GPU is available
)
```

## Performance

### CPU Mode (Default)
- **Speed**: ~15-20 seconds per sentence
- **Quality**: High (identical to GPU)
- **RAM Usage**: ~2-3 GB
- **Model Load Time**: ~5-10 seconds (first run only)

### GPU Acceleration (Future)
Currently disabled due to GPU compatibility issues (RTX 5060 Ti requires newer PyTorch builds). CPU mode is the recommended configuration.

**Potential GPU Support:**
- Intel Arc B580 via Intel Extension for PyTorch (experimental)
- NVIDIA GPUs with sm_90 or earlier compute capability

## Troubleshooting

### "No module named TTS"
```bash
pip install TTS==0.22.0
```

### "GPT2InferenceModel object has no attribute 'generate'"
```bash
pip install transformers==4.46.0
```

### Voice sounds hollow or broken
1. Check voice sample quality (run diagnostic in `text_to_voice.py`)
2. Optimize your voice sample using `optimize_voice_sample.py`
3. Ensure sample is 10-15 seconds and 22050 Hz

### CUDA errors
The system automatically falls back to CPU mode. To force CPU:
```python
# Set environment variable before running
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
```

### Slow generation
- First generation is always slower (model loading)
- Subsequent generations use cached model (~15s per sentence)
- Consider using streaming mode for long texts

## Technical Details

### Model Information

- **Model**: Coqui TTS XTTS v2
- **Architecture**: GPT-2 based autoregressive model
- **Size**: ~2 GB
- **Voice Cloning**: Zero-shot (no training required)
- **Download**: Automatic on first run (cached locally)

### Audio Pipeline

1. Text preprocessing (emoji removal, cleanup)
2. Voice cloning with XTTS v2
3. Audio generation (22050 Hz, mono WAV)
4. Device selection (VB-Cable or default)
5. Playback via sounddevice
6. Cleanup (temporary file deletion)

### File Structure

```
BASE/tools/
├── text_to_voice.py           # Main TTS module
├── optimize_voice_sample.py   # Voice sample optimizer
personality/voice/
├── Anna_Voice_Sample_a.mp3    # Original voice sample
└── Anna_Voice_Sample_optimized.wav  # Optimized sample
```

## Migration from System TTS

The previous implementation used `pyttsx3` with system voices. Key differences:

| Feature | Old (pyttsx3) | New (XTTS v2) |
|---------|---------------|---------------|
| Voice Quality | Robotic, synthetic | Natural, human-like |
| Customization | Limited (pitch, rate) | Full voice cloning |
| Setup | Simple | Requires Python 3.11 |
| Performance | Fast (~1s) | Moderate (~15s CPU) |
| Dependencies | Minimal | PyTorch, TTS models |
| Voice Options | System voices only | Any voice sample |

To revert to the old system, use the backup file:
```bash
cp text_to_voice_old.py text_to_voice.py
```

## Future Enhancements

- [ ] GPU acceleration for RTX 5060 Ti (awaiting PyTorch sm_120 support)
- [ ] Intel Arc B580 XPU support via Intel Extension for PyTorch
- [ ] Real-time streaming for longer responses
- [ ] Voice emotion/style control
- [ ] Multiple voice profiles
- [ ] Background voice generation (non-blocking)

## References

- [Coqui TTS Documentation](https://github.com/coqui-ai/TTS)
- [XTTS v2 Paper](https://arxiv.org/abs/2406.04904)
- [VB-Cable Download](https://vb-audio.com/Cable/)
- [PyTorch Installation Guide](https://pytorch.org/get-started/locally/)