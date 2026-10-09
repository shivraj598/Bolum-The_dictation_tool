#!/usr/bin/env python3
"""
Parakeet TDT 0.6B v3 - MLX Voice Dictation Test Script
Run with: source venv/bin/activate && python test_parakeet.py
"""

import mlx.core as mx
import mlx.nn as nn
from mlx_audio.stt import load
import sounddevice as sd
import numpy as np
import time
import argparse

# Model path
MODEL_PATH = "parakeet-tdt-0.6b-v3"

def load_model():
    print("Loading Parakeet TDT 0.6B v3...")
    start = time.time()
    model = load(MODEL_PATH)
    print(f"Model loaded in {time.time() - start:.2f}s")
    print(f"Model type: {type(model).__name__}")
    return model

def transcribe_audio(model, audio_data, sample_rate=16000):
    """Transcribe audio using Parakeet model."""
    # Ensure audio is float32 and normalized
    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32)
    
    # Resample if needed (Parakeet expects 16kHz)
    if sample_rate != 16000:
        import scipy.signal
        audio_data = scipy.signal.resample(
            audio_data, 
            int(len(audio_data) * 16000 / sample_rate)
        )
        sample_rate = 16000
    
    # Convert to MLX array
    audio_mx = mx.array(audio_data)
    
    print("Transcribing...")
    start = time.time()
    # The model.generate() method takes audio and returns text
    result = model.generate(audio_mx)
    print(f"Transcription took {time.time() - start:.2f}s")
    
    # Extract text from result
    if isinstance(result, list):
        text = " ".join([r.text for r in result])
    else:
        text = result.text if hasattr(result, 'text') else str(result)
    
    return text

def record_audio(duration, sample_rate=16000):
    """Record audio from microphone."""
    print(f"Recording for {duration} seconds...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    return audio.flatten()

def main():
    parser = argparse.ArgumentParser(description="Parakeet TDT Voice Dictation Test")
    parser.add_argument("--duration", "-d", type=int, default=5, help="Recording duration in seconds")
    parser.add_argument("--sample-rate", "-r", type=int, default=16000, help="Sample rate")
    parser.add_argument("--continuous", "-c", action="store_true", help="Continuous recording (Ctrl+C to stop)")
    args = parser.parse_args()

    model = load_model()
    
    if args.continuous:
        print("Continuous recording mode. Press Ctrl+C to stop.")
        sample_rate = args.sample_rate
        chunk_duration = 5  # Process in 5-second chunks
        
        try:
            while True:
                audio = record_audio(chunk_duration, sample_rate)
                text = transcribe_audio(model, audio, sample_rate)
                if text.strip():
                    print(f"> {text.strip()}")
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        audio = record_audio(args.duration, args.sample_rate)
        text = transcribe_audio(model, audio, args.sample_rate)
        print(f"\nTranscription: {text}")

if __name__ == "__main__":
    main()