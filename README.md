# Bolum - Voice Dictation Tool

A voice dictation toolkit with two backends:
1. **Rust + whisper.cpp** - Ultra-lightweight (39MB model, runs on 4GB RAM)
2. **Python + MLX Parakeet** - High-accuracy on Apple Silicon (requires 8GB+ RAM)

## Quick Start (Rust - Low-end devices)

```bash
git clone https://github.com/shivraj598/Bolum
cd Bolum
cargo build --release
./target/release/bolum --duration 10
```

## Quick Start (Python/MLX - Apple Silicon Mac)

```bash
cd Bolum
python3 -m venv venv
source venv/bin/activate
pip install mlx mlx-audio huggingface_hub
# Model downloads automatically on first run (~2.5GB)
python test_parakeet.py --duration 10
```

---

## Backend Comparison

| Aspect | Rust (whisper.cpp) | Python (MLX Parakeet) |
|--------|-------------------|----------------------|
| **Model Size** | 39-244 MB | ~2.5 GB |
| **RAM Usage** | ~150-800 MB | ~3-4 GB |
| **Min RAM** | 4 GB | 8 GB |
| **Accuracy** | Good | Excellent |
| **Speed** | Real-time | Near real-time |
| **Platform** | Cross-platform | macOS (Apple Silicon) |
| **Language** | 99+ languages | English primary |

---

## Rust Backend (Production - Low-end devices)

### Models

| Model | Size | RAM | Best For |
|-------|------|-----|----------|
| `tiny` | 39 MB | ~150 MB | 4GB RAM, real-time |
| `base` | 74 MB | ~300 MB | Balanced |
| `small` | 244 MB | ~800 MB | 8GB+ RAM |

### Usage

```bash
# List models
./target/release/bolum --list-models

# Record 10 seconds
./target/release/bolum --duration 10

# Continuous (Ctrl+C to stop)
./target/release/bolum

# Better accuracy
./target/release/bolum --model base --duration 30

# Save to file
./target/release/bolum --output transcript.txt --duration 60
```

---

## Python/MLX Backend (Testing - Apple Silicon)

### Requirements
- macOS on Apple Silicon (M1/M2/M3)
- 8GB+ RAM recommended
- Python 3.10+

### Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Test Script (`test_parakeet.py`)
```bash
# Record 10 seconds
python test_parakeet.py --duration 10

# Continuous dictation
python test_parakeet.py --continuous
```

### Model
- **Parakeet TDT 0.6B v3** (`mlx-community/parakeet-tdt-0.6b-v3`)
- ~627M parameters, ~2.5GB on disk
- Auto-downloads to `parakeet-tdt-0.6b-v3/` on first run

---

## Architecture

### Rust (whisper.cpp)
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

### Python (MLX Parakeet)
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Audio     │────▶│  Transcriber │────▶│   Output    │
│  Recorder   │     │ (MLX Parakeet)     │  (stdout)   │
│ (sounddevice)     │              │     │             │
└─────────────┘     └──────────────┘     └─────────────┘
       │                    │
       ▼                    ▼
  16kHz mono         MLX unified
  f32 samples        memory (Metal)
```

---

## Requirements

### Rust
- Rust 1.75+
- Audio input device
- ~100MB disk space

### Python/MLX
- macOS on Apple Silicon
- Python 3.10+
- 8GB+ RAM
- ~3GB disk space

---

## License

MIT