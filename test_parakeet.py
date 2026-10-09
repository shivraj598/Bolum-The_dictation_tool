#!/usr/bin/env python3
"""
Parakeet TDT 0.6B v3 - Push-to-Talk Voice Dictation
Supports key combinations like Option+Space, Ctrl+Space, etc.

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
# Default: Option + Space (left or right option)
TRIGGER_KEYS = {keyboard.Key.alt, keyboard.Key.space}  
TOGGLE_MODE = True  # True = press combo once to start, press again to stop
# ===================================

class PushToTalkDictation:
    def __init__(self, model, trigger_keys=TRIGGER_KEYS, toggle_mode=TOGGLE_MODE):
        self.model = model
        self.trigger_keys = set(trigger_keys)
        self.toggle_mode = toggle_mode
        
        self.recording = False
        self.audio_queue = queue.Queue()
        self.audio_buffer = []
        self.stream = None
        self.listener = None
        
        # For toggle mode
        self.toggle_state = False
        
        # Track currently pressed keys
        self.pressed_keys = set()
        
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
        print(f"\n🎙️  RECORDING... (press {self.get_keys_name()} again to stop)")
    
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
    
    def get_keys_name(self):
        """Get human-readable key combination name."""
        names = []
        for k in self.trigger_keys:
            if hasattr(k, 'name'):
                names.append(k.name.upper())
            else:
                names.append(str(k).upper())
        return " + ".join(names)
    
    def check_trigger(self):
        """Check if all trigger keys are currently pressed."""
        return self.trigger_keys.issubset(self.pressed_keys)
    
    def on_press(self, key):
        """Handle key press."""
        self.pressed_keys.add(key)
        
        if self.check_trigger():
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
                            self.copy_to_clipboard(text)
            else:
                # Hold mode - start recording
                self.start_recording()
    
    def on_release(self, key):
        """Handle key release."""
        # Check trigger before removing the key
        trigger_was_pressed = self.check_trigger()
        
        self.pressed_keys.discard(key)
        
        if not self.toggle_mode and trigger_was_pressed and not self.check_trigger():
            # Hold mode - stop recording when trigger released
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
        print(f"\n{'='*55}")
        print(f"  Push-to-Talk Dictation (Parakeet TDT 0.6B)")
        print(f"{'='*55}")
        print(f"  Trigger: {self.get_keys_name()}")
        print(f"  Mode: {'Toggle (press combo on/off)' if self.toggle_mode else 'Hold combo to record'}")
        print(f"  Sample rate: {SAMPLE_RATE}Hz")
        print(f"{'='*55}")
        print(f"\nReady. Press {self.get_keys_name()} to start dictating.")
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

def parse_key_combo(combo_str):
    """Parse key combination string like 'alt+space' or 'ctrl+shift+space'."""
    key_map = {
        'f1': keyboard.Key.f1, 'f2': keyboard.Key.f2, 'f3': keyboard.Key.f3,
        'f4': keyboard.Key.f4, 'f5': keyboard.Key.f5, 'f6': keyboard.Key.f6,
        'f7': keyboard.Key.f7, 'f8': keyboard.Key.f8, 'f9': keyboard.Key.f9,
        'f10': keyboard.Key.f10, 'f11': keyboard.Key.f11, 'f12': keyboard.Key.f12,
        'f13': keyboard.Key.f13, 'f14': keyboard.Key.f14, 'f15': keyboard.Key.f15,
        'space': keyboard.Key.space,
        'ctrl': keyboard.Key.ctrl, 'ctrl_l': keyboard.Key.ctrl, 'ctrl_r': keyboard.Key.ctrl_r,
        'alt': keyboard.Key.alt, 'alt_l': keyboard.Key.alt, 'alt_r': keyboard.Key.alt_r,
        'option': keyboard.Key.alt, 'option_l': keyboard.Key.alt, 'option_r': keyboard.Key.alt_r,
        'shift': keyboard.Key.shift, 'shift_l': keyboard.Key.shift, 'shift_r': keyboard.Key.shift_r,
        'cmd': keyboard.Key.cmd, 'cmd_l': keyboard.Key.cmd, 'cmd_r': keyboard.Key.cmd_r,
        'super': keyboard.Key.cmd, 'super_l': keyboard.Key.cmd, 'super_r': keyboard.Key.cmd_r,
        'enter': keyboard.Key.enter, 'tab': keyboard.Key.tab,
    }
    
    keys = set()
    for part in combo_str.lower().split('+'):
        part = part.strip()
        if part in key_map:
            keys.add(key_map[part])
        else:
            print(f"Warning: Unknown key '{part}', ignoring")
    return keys

def main():
    parser = argparse.ArgumentParser(description="Push-to-Talk Voice Dictation with Parakeet")
    parser.add_argument("--key", "-k", default="alt+space", 
                        help="Trigger key combination (e.g., 'alt+space', 'ctrl+space', 'cmd+space', 'f13')")
    parser.add_argument("--hold", action="store_true", help="Hold mode (hold combo to record, release to stop)")
    parser.add_argument("--list-keys", action="store_true", help="List available keys and exit")
    args = parser.parse_args()
    
    if args.list_keys:
        print("Available keys: f1-f15, space, ctrl/ctrl_l/ctrl_r, alt/alt_l/alt_r (option), shift/shift_l/shift_r, cmd/cmd_l/cmd_r (super), enter, tab")
        print("Combine with + : alt+space, ctrl+shift+space, etc.")
        return
    
    trigger_keys = parse_key_combo(args.key)
    if not trigger_keys:
        trigger_keys = TRIGGER_KEYS
    
    toggle_mode = not args.hold
    
    model = load_model()
    app = PushToTalkDictation(model, trigger_keys, toggle_mode)
    app.run()

if __name__ == "__main__":
    main()