use anyhow::{Context, Result};
use std::path::Path;
use whisper_rs::{FullParams, SamplingStrategy, WhisperContext, WhisperContextParameters};

pub struct Transcriber {
    ctx: WhisperContext,
    language: String,
}

impl Transcriber {
    pub fn new<P: AsRef<Path>>(model_path: P, language: String) -> Result<Self> {
        let ctx = WhisperContext::new_with_params(
            model_path.as_ref().to_str().context("Invalid model path")?,
            WhisperContextParameters::default(),
        )
        .context("Failed to load whisper model")?;

        Ok(Self { ctx, language })
    }

    pub async fn transcribe(&self, audio: &[f32]) -> Result<String> {
        let mut state = self.ctx.create_state().context("Failed to create whisper state")?;

        let mut params = FullParams::new(SamplingStrategy::Greedy { best_of: 1 });

        params.set_language(Some(&self.language));
        params.set_translate(false);
        params.set_print_progress(false);
        params.set_print_realtime(false);
        params.set_print_timestamps(false);
        params.set_no_timestamps(true);

        state.full(params, audio).context("Failed to run transcription")?;

        let num_segments = state.full_n_segments() as usize;

        let mut transcript = String::new();
        for i in 0..num_segments {
            if let Some(segment) = state.get_segment(i as i32) {
                if let Ok(text) = segment.to_str() {
                    transcript.push_str(text);
                    transcript.push(' ');
                }
            }
        }

        Ok(transcript.trim().to_string())
    }
}