#!/usr/bin/env python3
"""
Bolum - Menu Bar Voice Dictation App
Native macOS menu bar app using MLX Parakeet TDT 0.6B v3
Run: source venv/bin/activate && python bolum_menubar.py
"""

import rumps
import mlx.core as mx
from mlx_audio.stt import load
import sounddevice as sd
import numpy as np
import threading
import time
import pyperclip
from pynput import keyboard

# ========== CONFIG ==========
MODEL_PATH = "parakeet-tdt-0.6b-v3"
SAMPLE_RATE = 16000
TRIGGER_COMBO = {keyboard.Key.alt, keyboard.Key.space}  # Option + Space
# ============================

class BolumApp(rumps.App):
    def __init__(self):
        super().__init__("🎙️", quit_button=None)
        
        self.model = None
        self.model_loaded = False
        self.recording = False
        self.audio_queue = None
        self.audio_buffer = []
        self.stream = None
        self.listener = None
        self.pressed_keys = set()
        
        # Menu items
        self.menu = [
            rumps.MenuItem("Bolum Voice Dictation", callback=None),
            rumps.separator,
            rumps.MenuItem("Load Model", callback=self.load_model),
            rumps.MenuItem("Start Dictation (Option+Space)", callback=self.toggle_dictation),
            rumps.separator,
            rumps.MenuItem("Settings", callback=None),
            rumps.MenuItem("  Model: Parakeet TDT 0.6B", callback=None),
            rumps.MenuItem("  Trigger: Option + Space", callback=None),
            rumps.MenuItem("  Mode: Toggle", callback=None),
            rumps.separator,
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        
        # Start keyboard listener
        self.start_keyboard_listener()
        
        # Load model in background
        threading.Thread(target=self.load_model_async, daemon=True).start()
    
    def load_model_async(self):
        """Load model in background thread."""
        rumps.notification("Bolum", "Loading model...", "Please wait")
        start = time.time()
        self.model = load(MODEL_PATH)
        self.model_loaded = True
        elapsed = time.time() - start
        rumps.notification("Bolum", "Ready!", f"Model loaded in {elapsed:.1f}s. Press Option+Space to dictate.")
        self.update_menu()
    
    def update_menu(self):
        """Update menu item states."""
        if self.model_loaded:
            self.menu["Load Model"].title = "✅ Model Loaded"
            self.menu["Load Model"].set_callback(None)
            self.menu["Start Dictation (Option+Space)"].title = "🎙️ Dictation Ready (Option+Space)"
        else:
            self.menu["Load Model"].title = "⏳ Loading Model..."
    
    def load_model(self, _):
        """Manual model load trigger."""
        if not self.model_loaded:
            threading.Thread(target=self.load_model_async, daemon=True).start()
    
    def toggle_dictation(self, _):
        """Toggle dictation on/off."""
        if not self.model_loaded:
            rumps.notification("Bolum", "Model not loaded", "Please wait for model to load")
            return
        self.toggle_recording()
    
    def start_keyboard_listener(self):
        """Start global keyboard listener."""
        self.listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.listener.start()
    
    def check_trigger(self):
        """Check if trigger combo is pressed."""
        return TRIGGER_COMBO.issubset(self.pressed_keys)
    
    def on_key_press(self, key):
        self.pressed_keys.add(key)
        if self.check_trigger():
            self.toggle_recording()
    
    def on_key_release(self, key):
        self.pressed_keys.discard(key)
    
    def toggle_recording(self):
        """Start or stop recording."""
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Start audio recording."""
        if self.recording or not self.model_loaded:
            return
        
        self.recording = True
        self.audio_buffer = []
        self.audio_queue = []
        
        def audio_callback(indata, frames, time_info, status):
            if self.recording:
                self.audio_queue.append(indata.copy().flatten())
        
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype='float32',
            callback=audio_callback,
            blocksize=1024
        )
        self.stream.start()
        
        # Update menu
        self.menu["Start Dictation (Option+Space)"].title = "🔴 Recording... (Option+Space to stop)"
        rumps.notification("Bolum", "Recording started", "Speak now...")
    
    def stop_recording(self):
        """Stop recording and transcribe."""
        if not self.recording:
            return
        
        self.recording = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        if not self.audio_queue:
            self.menu["Start Dictation (Option+Space)"].title = "🎙️ Dictation Ready (Option+Space)"
            return
        
        # Update menu
        self.menu["Start Dictation (Option+Space)"].title = "⏳ Transcribing..."
        
        # Transcribe in background
        threading.Thread(target=self.transcribe_audio, daemon=True).start()
    
    def transcribe_audio(self):
        """Transcribe recorded audio."""
        try:
            # Concatenate audio
            audio = np.concatenate(self.audio_queue)
            duration = len(audio) / SAMPLE_RATE
            
            if duration < 0.5:
                rumps.notification("Bolum", "Too short", "Recording too short, ignored")
                self.update_menu_title()
                return
            
            # Convert to MLX array
            audio_mx = mx.array(audio.astype(np.float32))
            
            # Transcribe
            start = time.time()
            result = self.model.generate(audio_mx)
            elapsed = time.time() - start
            
            # Extract text
            if isinstance(result, list):
                text = " ".join([r.text for r in result])
            else:
                text = result.text if hasattr(result, 'text') else str(result)
            
            text = text.strip()
            
            if text:
                # Copy to clipboard
                pyperclip.copy(text)
                
                # Show notification with text
                display_text = text[:100] + "..." if len(text) > 100 else text
                rumps.notification(
                    "Bolum - Transcribed", 
                    f"{duration:.1f}s in {elapsed:.2f}s", 
                    display_text
                )
                
                # Also print to console for debugging
                print(f"\n📝 {text}\n")
            else:
                rumps.notification("Bolum", "No speech detected", "Try speaking louder")
        
        except Exception as e:
            rumps.notification("Bolum", "Error", str(e))
            print(f"Error: {e}")
        
        finally:
            self.update_menu_title()
    
    def update_menu_title(self):
        """Update menu title back to ready state."""
        if self.model_loaded:
            self.menu["Start Dictation (Option+Space)"].title = "🎙️ Dictation Ready (Option+Space)"

    @rumps.clicked("Quit")
    def quit_app(self, _):
        if self.listener:
            self.listener.stop()
        if self.stream:
            self.stream.stop()
            self.stream.close()
        rumps.quit_application()

if __name__ == "__main__":
    app = BolumApp()
    app.run()