use anyhow::{Context, Result};
use std::path::{Path, PathBuf};
use tokio::fs;

const MODEL_URLS: &[(&str, &str)] = &[
    ("tiny", "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin"),
    ("tiny-multilingual", "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin"),
    ("base", "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin"),
    ("base-multilingual", "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"),
    ("small", "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin"),
    ("small-multilingual", "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"),
];

pub struct ModelManager {
    models_dir: PathBuf,
}

impl ModelManager {
    pub fn new() -> Result<Self> {
        let models_dir = dirs::data_dir()
            .context("Could not find data directory")?
            .join("bolum")
            .join("models");

        fs::create_dir_all(&models_dir).await?;
        Ok(Self { models_dir })
    }

    pub fn list_available_models() {
        println!("Available models:");
        for (name, url) in MODEL_URLS {
            let size = estimate_model_size(name);
            println!("  {} - {} ({})", name, url, size);
        }
    }

    pub async fn ensure_model(&self, name: &str) -> Result<PathBuf> {
        let model_path = self.models_dir.join(format!("ggml-{}.bin", name));

        if model_path.exists() {
            tracing::info!("Model found at: {}", model_path.display());
            return Ok(model_path);
        }

        let url = MODEL_URLS
            .iter()
            .find(|(n, _)| *n == name)
            .map(|(_, u)| *u)
            .context(format!("Unknown model: {}", name))?;

        tracing::info!("Downloading model {} from {}", name, url);
        self.download_model(url, &model_path).await?;

        Ok(model_path)
    }

    async fn download_model(&self, url: &str, path: &Path) -> Result<()> {
        let client = reqwest::Client::new();
        let response = client.get(url).send().await?.error_for_status()?;

        let mut file = fs::File::create(path).await?;
        let mut stream = response.bytes_stream();

        use futures_util::StreamExt;
        while let Some(chunk) = stream.next().await {
            let chunk = chunk?;
            tokio::io::AsyncWriteExt::write_all(&mut file, &chunk).await?;
        }

        tracing::info!("Model downloaded to: {}", path.display());
        Ok(())
    }
}

fn estimate_model_size(name: &str) -> &'static str {
    match name {
        "tiny" | "tiny-multilingual" => "~39 MB",
        "base" | "base-multilingual" => "~74 MB",
        "small" | "small-multilingual" => "~244 MB",
        _ => "Unknown",
    }
}