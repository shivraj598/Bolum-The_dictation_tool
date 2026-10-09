#!/usr/bin/env python3
"""
Debug key detection on macOS
"""
from pynput import keyboard

print("Press keys to see what pynput detects. Press Ctrl+C to exit.\n")

def on_press(key):
    print(f"PRESS: {key} | type: {type(key)} | repr: {repr(key)}")

def on_release(key):
    print(f"RELEASE: {key}")

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    try:
        listener.join()
    except KeyboardInterrupt:
        pass