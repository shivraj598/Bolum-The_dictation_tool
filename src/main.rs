use anyhow::Result;
use clap::Parser;
use std::path::PathBuf;
use tracing::{info, warn};

mod audio;
mod config;
mod model;
mod transcriber;

use audio::AudioRecorder;
use config::Config;
use model::ModelManager;
use transcriber::Transcriber;

#[derive(Parser, Debug)]
#[command(name = "bolum", version, about = "Voice dictation tool for low-end devices")]
struct Args {
    /// Model to use (tiny, base, small)
    #[arg(short, long, default_value = "tiny")]
    model: String,

    /// Language code (e.g., en, auto)
    #[arg(short, long, default_value = "auto")]
    language: String,

    /// Output file for transcription
    #[arg(short, long)]
    output: Option<PathBuf>,

    /// List available models and exit
    #[arg(long)]
    list_models: bool,

    /// Record duration in seconds (0 = continuous until Ctrl+C)
    #[arg(short, long, default_value = "0")]
    duration: u32,

    /// Use VAD (Voice Activity Detection)
    #[arg(long, default_value = "true")]
    vad: bool,

    /// Sample rate for recording
    #[arg(long, default_value = "16000")]
    sample_rate: u32,
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    let args = Args::parse();

    let config = Config {
        model_name: args.model,
        language: args.language,
        output_file: args.output,
        list_models: args.list_models,
        duration: args.duration,
        use_vad: args.vad,
        sample_rate: args.sample_rate,
    };

    if config.list_models {
        ModelManager::list_available_models();
        return Ok(());
    }

    info!("Starting Bolum voice dictation...");
    info!("Model: {}", config.model_name);
    info!("Language: {}", config.language);

    let model_manager = ModelManager::new()?;
    let model_path = model_manager.ensure_model(&config.model_name).await?;

    let transcriber = Transcriber::new(model_path, config.language.clone())?;
    let recorder = AudioRecorder::new(config.sample_rate)?;

    info!("Ready. Press Ctrl+C to stop recording.");

    let transcript = if config.duration > 0 {
        recorder.record_for_duration(config.duration, &transcriber).await?
    } else {
        recorder.record_continuous(&transcriber).await?
    };

    if let Some(output_path) = config.output_file {
        std::fs::write(&output_path, &transcript)?;
        info!("Transcription saved to: {}", output_path.display());
    } else {
        println!("\n--- Transcription ---");
        println!("{}", transcript);
    }

    Ok(())
}