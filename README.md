# Bolum - Voice Dictation Tool

A lightweight, offline speech-to-text application built in Rust using whisper.cpp. Designed for low-end devices (4GB RAM) with models as small as 39MB.

## Features

- 🎙️ Real-time voice dictation
- 📱 Runs on 4GB RAM devices
- 🔒 Fully offline - no cloud API calls
- ⚡ Optimized CPU inference via whisper.cpp
- 🦀 Native Rust performance
- 📦 Tiny models: tiny.en (39MB), base.en (74MB)

## Installation

### Pre-built binaries
```bash
# Coming soon via GitHub Releases
```

### Build from source
```bash
# Requires Rust 1.75+
git clone https://github.com/shivraj598/Bolum
cd Bolum
cargo build --release
./target/release/bolum --help
```

## Usage

```bash
# List available models
bolum --list-models

# Record for 10 seconds with tiny model (default)
bolum --duration 10

# Continuous recording (Ctrl+C to stop)
bolum

# Use base model for better accuracy
bolum --model base --duration 30

# Save transcription to file
bolum --output transcript.txt --duration 60

# Specify language (auto-detect by default)
bolum --language en --duration 30
```

## Models

| Model | Size | Speed | Accuracy | Best For |
|-------|------|-------|----------|----------|
| tiny.en | 39 MB | Fastest | Good | 4GB RAM, real-time |
| base.en | 74 MB | Fast | Better | Balanced |
| small.en | 244 MB | Moderate | Best | 8GB+ RAM |

Models are downloaded automatically on first use to `~/.local/share/bolum/models/` (Linux/macOS) or `%APPDATA%\bolum\models\` (Windows).

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Audio     │────▶│  Transcriber │────▶│   Output    │
│  Recorder   │     │ (whisper-rs) │     │  (stdout/   │
│  (cpal)     │     │              │     │   file)     │
└─────────────┘     └──────────────┘     └─────────────┘
       │                    │
       ▼                    ▼
  16kHz mono         GGML models
  f32 samples        (quantized)
```

## Requirements

- Rust 1.75+
- Audio input device (microphone)
- ~100MB disk space for models

## License

MIT