from setuptools import setup

APP = ['bolum_menubar.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': None,
    'plist': {
        'CFBundleName': 'Bolum',
        'CFBundleDisplayName': 'Bolum',
        'CFBundleIdentifier': 'com.shivraj598.bolum',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'LSUIElement': True,  # Menu bar app (no dock icon)
        'NSMicrophoneUsageDescription': 'Bolum needs microphone access for voice dictation',
        'NSHighResolutionCapable': True,
    },
    'packages': ['mlx', 'mlx_audio', 'rumps', 'pyperclip', 'pynput', 'sounddevice', 'numpy', 'scipy', 'huggingface_hub'],
    'includes': ['mlx_audio.stt.models.parakeet'],
    'excludes': ['tkinter', 'matplotlib', 'PIL', 'cv2'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)