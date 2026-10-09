use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub model_name: String,
    pub language: String,
    pub output_file: Option<PathBuf>,
    pub list_models: bool,
    pub duration: u32,
    pub use_vad: bool,
    pub sample_rate: u32,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            model_name: "tiny".to_string(),
            language: "auto".to_string(),
            output_file: None,
            list_models: false,
            duration: 0,
            use_vad: true,
            sample_rate: 16000,
        }
    }
}