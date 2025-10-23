import soundfile as sf
import librosa
import numpy as np
import os

def optimize_voice_sample(input_path, output_path, target_duration=12, target_sr=22050):
    """
    Optimize voice sample for XTTS voice cloning
    
    Args:
        input_path: Path to original voice sample
        output_path: Path to save optimized sample
        target_duration: Target duration in seconds (10-15 recommended)
        target_sr: Target sample rate (22050 for XTTS)
    """
    print(f"Loading: {input_path}")
    
    # Load audio
    audio, sr = librosa.load(input_path, sr=None, mono=True)
    duration = len(audio) / sr
    
    print(f"Original: {sr}Hz, {duration:.1f}s")
    
    # Trim silence from beginning and end
    audio_trimmed, _ = librosa.effects.trim(audio, top_db=30)
    
    # If longer than target, take middle portion (usually has better prosody)
    if len(audio_trimmed) > target_duration * sr:
        start_sample = int((len(audio_trimmed) - target_duration * sr) / 2)
        end_sample = start_sample + int(target_duration * sr)
        audio_trimmed = audio_trimmed[start_sample:end_sample]
        print(f"Trimmed to {target_duration}s (middle section)")
    
    # Resample to target sample rate
    if sr != target_sr:
        audio_resampled = librosa.resample(audio_trimmed, orig_sr=sr, target_sr=target_sr)
        print(f"Resampled: {sr}Hz -> {target_sr}Hz")
    else:
        audio_resampled = audio_trimmed
    
    # Normalize audio to prevent clipping
    audio_normalized = audio_resampled / np.max(np.abs(audio_resampled)) * 0.95
    
    # Save optimized version
    sf.write(output_path, audio_normalized, target_sr)
    
    final_duration = len(audio_normalized) / target_sr
    print(f"Saved: {output_path}")
    print(f"Final: {target_sr}Hz, {final_duration:.1f}s")
    print("\n✓ Voice sample optimized!")

if __name__ == "__main__":
    INPUT_SAMPLE = "./../../personality/voice/Anna_Voice_Sample_a.mp3"
    OUTPUT_SAMPLE = "./../../personality/voice/Anna_Voice_Sample_optimized.wav"
    
    optimize_voice_sample(INPUT_SAMPLE, OUTPUT_SAMPLE, target_duration=12, target_sr=22050)
    
    print("\n" + "="*50)
    print("Now update your code to use the optimized sample:")
    print(f'VOICE_SAMPLE = "{OUTPUT_SAMPLE}"')
    print("="*50)