use anyhow::{Context, Result};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{SampleFormat, StreamConfig};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tokio::sync::mpsc;
use tracing::{debug, info, warn};

use crate::transcriber::Transcriber;

pub struct AudioRecorder {
    sample_rate: u32,
    channels: u16,
}

impl AudioRecorder {
    pub fn new(sample_rate: u32) -> Result<Self> {
        Ok(Self {
            sample_rate,
            channels: 1,
        })
    }

    pub async fn record_for_duration(
        &self,
        duration_secs: u32,
        transcriber: &Transcriber,
    ) -> Result<String> {
        let (tx, mut rx) = mpsc::channel::<Vec<f32>>(100);
        let transcriber = Arc::new(transcriber.clone());
        let tx_clone = tx.clone();

        let host = cpal::default_host();
        let device = host
            .default_input_device()
            .context("No input device available")?;

        let config = StreamConfig {
            channels: self.channels,
            sample_rate: cpal::SampleRate(self.sample_rate),
            buffer_size: cpal::BufferSize::Default,
        };

        let err_fn = |err| warn!("Audio stream error: {}", err);

        let stream = device.build_input_stream(
            &config,
            move |data: &[f32], _: &cpal::InputCallbackInfo| {
                if tx_clone.try_send(data.to_vec()).is_err() {
                    debug!("Audio buffer full, dropping frame");
                }
            },
            err_fn,
            None,
        )?;

        stream.play()?;
        info!("Recording for {} seconds...", duration_secs);

        let mut all_audio = Vec::new();
        let start = std::time::Instant::now();
        let duration = Duration::from_secs(duration_secs as u64);

        while start.elapsed() < duration {
            if let Some(chunk) = rx.recv().await {
                all_audio.extend(chunk);
            }
        }

        drop(stream);
        drop(tx);

        info!("Recording complete. Transcribing...");
        transcriber.transcribe(&all_audio).await
    }

    pub async fn record_continuous(&self, transcriber: &Transcriber) -> Result<String> {
        let (tx, mut rx) = mpsc::channel::<Vec<f32>>(100);
        let transcriber = Arc::new(transcriber.clone());

        let host = cpal::default_host();
        let device = host
            .default_input_device()
            .context("No input device available")?;

        let config = StreamConfig {
            channels: self.channels,
            sample_rate: cpal::SampleRate(self.sample_rate),
            buffer_size: cpal::BufferSize::Default,
        };

        let err_fn = |err| warn!("Audio stream error: {}", err);

        let stream = device.build_input_stream(
            &config,
            move |data: &[f32], _: &cpal::InputCallbackInfo| {
                if tx.try_send(data.to_vec()).is_err() {
                    debug!("Audio buffer full, dropping frame");
                }
            },
            err_fn,
            None,
        )?;

        stream.play()?;
        info!("Recording continuously... Press Ctrl+C to stop.");

        let mut all_audio = Vec::new();
        let ctrl_c = tokio::signal::ctrl_c();
        tokio::pin!(ctrl_c);

        loop {
            tokio::select! {
                Some(chunk) = rx.recv() => {
                    all_audio.extend(chunk);
                }
                _ = &mut ctrl_c => {
                    info!("Stopping recording...");
                    break;
                }
            }
        }

        drop(stream);

        info!("Transcribing...");
        transcriber.transcribe(&all_audio).await
    }
}