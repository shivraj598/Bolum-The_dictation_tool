#!/usr/bin/env python3
"""
Parakeet TDT 0.6B v3 - Push-to-Talk Voice Dictation
Press and hold a key to record, release to transcribe.
Or press once to start, press again to stop (toggle mode).

Run: source venv/bin/activate && python test_parakeet.py
"""

import mlx.core as mx
from mlx_audio.stt import load
import sounddevice as sd
import numpy as np
import time
import argparse
import threading
import queue
from pynput import keyboard

# ========== CONFIGURATION ==========
MODEL_PATH = "parakeet-tdt-0.6b-v3"
SAMPLE_RATE = 16000
TRIGGER_KEY = keyboard.Key.f13  # Change this: keyboard.Key.f13, keyboard.Key.space, keyboard.Key.ctrl_r, etc.
TOGGLE_MODE = False  # True = press once to start, press again to stop. False = hold to record.
# ===================================

class PushToTalkDictation:
    def __init__(self, model, trigger_key=TRIGGER_KEY, toggle_mode=TOGGLE_MODE):
        self.model = model
        self.trigger_key = trigger_key
        self.toggle_mode = toggle_mode
        
        self.recording = False
        self.audio_queue = queue.Queue()
        self.audio_buffer = []
        self.stream = None
        self.listener = None
        
        # For toggle mode
        self.toggle_state = False
        
    def audio_callback(self, indata, frames, time_info, status):
        """Called by sounddevice for each audio chunk."""
        if self.recording:
            self.audio_queue.put(indata.copy().flatten())
    
    def start_recording(self):
        """Start audio stream."""
        if self.recording:
            return
            
        self.recording = True
        self.audio_buffer = []
        
        # Clear queue
        while not self.audio_queue.empty():
            self.audio_queue.get()
        
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype='float32',
            callback=self.audio_callback,
            blocksize=1024
        )
        self.stream.start()
        print(f"\n🎙️  RECORDING... (release {self.get_key_name()} to stop)")
    
    def stop_recording(self):
        """Stop audio stream and return recorded audio."""
        if not self.recording:
            return None
            
        self.recording = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        # Collect all audio from queue
        while not self.audio_queue.empty():
            self.audio_buffer.append(self.audio_queue.get())
        
        if not self.audio_buffer:
            print("No audio recorded.")
            return None
            
        audio = np.concatenate(self.audio_buffer)
        print(f"⏹️  Stopped. Recorded {len(audio)/SAMPLE_RATE:.1f}s. Transcribing...")
        return audio
    
    def transcribe(self, audio):
        """Transcribe audio using Parakeet model."""
        if audio is None or len(audio) == 0:
            return ""
        
        # Convert to MLX array
        audio_mx = mx.array(audio.astype(np.float32))
        
        start = time.time()
        result = self.model.generate(audio_mx)
        elapsed = time.time() - start
        
        # Extract text from result
        if isinstance(result, list):
            text = " ".join([r.text for r in result])
        else:
            text = result.text if hasattr(result, 'text') else str(result)
        
        print(f"✅ Transcribed in {elapsed:.2f}s: '{text}'")
        return text.strip()
    
    def get_key_name(self):
        """Get human-readable key name."""
        if hasattr(self.trigger_key, 'name'):
            return self.trigger_key.name.upper()
        return str(self.trigger_key)
    
    def on_press(self, key):
        """Handle key press."""
        if key == self.trigger_key:
            if self.toggle_mode:
                if not self.toggle_state:
                    self.toggle_state = True
                    self.start_recording()
                else:
                    self.toggle_state = False
                    audio = self.stop_recording()
                    if audio is not None:
                        text = self.transcribe(audio)
                        if text:
                            print(f"\n📝 {text}\n")
                            # Copy to clipboard (optional)
                            self.copy_to_clipboard(text)
            else:
                # Hold mode - start recording
                self.start_recording()
    
    def on_release(self, key):
        """Handle key release."""
        if key == self.trigger_key and not self.toggle_mode:
            audio = self.stop_recording()
            if audio is not None:
                text = self.transcribe(audio)
                if text:
                    print(f"\n📝 {text}\n")
                    self.copy_to_clipboard(text)
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        try:
            import subprocess
            subprocess.run(['pbcopy'], input=text.encode(), check=True)
            print("📋 Copied to clipboard!")
        except:
            pass
    
    def run(self):
        """Main loop."""
        print(f"\n{'='*50}")
        print(f"  Push-to-Talk Dictation (Parakeet TDT 0.6B)")
        print(f"{'='*50}")
        print(f"  Trigger key: {self.get_key_name()}")
        print(f"  Mode: {'Toggle (press on/off)' if self.toggle_mode else 'Hold to record'}")
        print(f"  Sample rate: {SAMPLE_RATE}Hz")
        print(f"{'='*50}")
        print(f"\nReady. Press {self.get_key_name()} to start dictating.")
        print(f"Press Ctrl+C to exit.\n")
        
        # Start keyboard listener
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.listener.start()
        
        try:
            # Keep running
            while self.listener.is_alive():
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nExiting...")
        finally:
            if self.listener:
                self.listener.stop()
            if self.stream:
                self.stream.stop()
                self.stream.close()

def load_model():
    print("Loading Parakeet TDT 0.6B v3...")
    start = time.time()
    model = load(MODEL_PATH)
    print(f"Model loaded in {time.time() - start:.2f}s")
    return model

def parse_key(key_str):
    """Parse key string to pynput Key."""
    key_map = {
        'f1': keyboard.Key.f1, 'f2': keyboard.Key.f2, 'f3': keyboard.Key.f3,
        'f4': keyboard.Key.f4, 'f5': keyboard.Key.f5, 'f6': keyboard.Key.f6,
        'f7': keyboard.Key.f7, 'f8': keyboard.Key.f8, 'f9': keyboard.Key.f9,
        'f10': keyboard.Key.f10, 'f11': keyboard.Key.f11, 'f12': keyboard.Key.f12,
        'f13': keyboard.Key.f13, 'f14': keyboard.Key.f14, 'f15': keyboard.Key.f15,
        'space': keyboard.Key.space, 'ctrl': keyboard.Key.ctrl, 'ctrl_r': keyboard.Key.ctrl_r,
        'alt': keyboard.Key.alt, 'alt_r': keyboard.Key.alt_r,
        'shift': keyboard.Key.shift, 'shift_r': keyboard.Key.shift_r,
        'cmd': keyboard.Key.cmd, 'cmd_r': keyboard.Key.cmd_r,
        'enter': keyboard.Key.enter, 'tab': keyboard.Key.tab,
    }
    return key_map.get(key_str.lower(), keyboard.Key.f13)

def main():
    parser = argparse.ArgumentParser(description="Push-to-Talk Voice Dictation with Parakeet")
    parser.add_argument("--key", "-k", default="f13", help="Trigger key (f1-f15, space, ctrl, alt, shift, cmd, enter, tab)")
    parser.add_argument("--toggle", "-t", action="store_true", help="Toggle mode (press once to start, press again to stop)")
    parser.add_argument("--list-keys", action="store_true", help="List available keys and exit")
    args = parser.parse_args()
    
    if args.list_keys:
        print("Available keys: f1-f15, space, ctrl, ctrl_r, alt, alt_r, shift, shift_r, cmd, cmd_r, enter, tab")
        return
    
    trigger_key = parse_key(args.key)
    toggle_mode = args.toggle
    
    model = load_model()
    app = PushToTalkDictation(model, trigger_key, toggle_mode)
    app.run()

if __name__ == "__main__":
    main()