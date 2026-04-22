//! chat.rs – Chat endpoint handlers

use axum::{
    extract::Json,
    http::StatusCode,
    response::{sse::{Event, Sse}, IntoResponse},
};
use futures::stream::{self, Stream};
use serde::{Deserialize, Serialize};
use std::convert::Infallible;
use tokio_stream::StreamExt as _;
use tracing::{error, info};
use uuid::Uuid;

// Import the bridged modules
use crate::pattern_matcher::{PatternMatcher, Stimulus};
use crate::retrieval_augmenter::{RetrievalAugmenter, RetrievalConfig};

#[derive(Debug, Deserialize)]
pub struct ChatRequest {
    pub participant_id: String,
    pub message: String,
    pub persona: Option<String>,
    pub session_id: Option<String>,
    pub stream: Option<bool>,
}

#[derive(Debug, Serialize)]
pub struct ChatResponse {
    pub response: String,
    pub persona: String,
    pub session_id: String,
    pub usage: Option<UsageStats>,
}

#[derive(Debug, Serialize)]
pub struct UsageStats {
    pub prompt_tokens: u32,
    pub completion_tokens: u32,
    pub total_tokens: u32,
}

pub async fn chat_handler(
    Json(payload): Json<ChatRequest>,
) -> Result<impl IntoResponse, (StatusCode, String)> {
    info!("Chat request from participant {}", payload.participant_id);

    // Initialize modules
    let matcher = PatternMatcher::new();
    let augmenter = RetrievalAugmenter::new(RetrievalConfig::default());

    let stimulus = Stimulus {
        content: payload.message.clone(),
        tags: vec!["chat".to_string()],
    };

    let system_1_response = matcher.match_stimulus(&stimulus);
    let persona = payload.persona.unwrap_or_else(|| "samara".to_string());
    
    let response_text = if system_1_response.confidence > 0.8 {
        system_1_response.text
    } else {
        match persona.as_str() {
            "samara" => format!("Hello! I'm Samara. You said: '{}'. How are you feeling today?", payload.message),
            "artery" => format!("Input received. Processing: '{}'. Awaiting further instructions.", payload.message),
            _ => format!("Message processed: '{}'", payload.message),
        }
    };

    let response = ChatResponse {
        response: response_text,
        persona,
        session_id: payload.session_id.unwrap_or_else(|| Uuid::new_v4().to_string()),
        usage: Some(UsageStats {
            prompt_tokens: payload.message.len() as u32 / 4,
            completion_tokens: payload.message.len() as u32 / 4,
            total_tokens: (payload.message.len() * 2) as u32 / 4,
        }),
    };

    Ok((StatusCode::OK, Json(response)))
}

pub async fn chat_stream_handler(
    Json(payload): Json<ChatRequest>,
) -> Sse<impl Stream<Item = Result<Event, Infallible>>> {
    info!("Streaming chat request from participant {}", payload.participant_id);

    let persona = payload.persona.unwrap_or_else(|| "samara".to_string());
    let words: Vec<String> = match persona.as_str() {
        "samara" => vec!["Hello", "there!", "I'm", "Samara.", "How", "can", "I", "help", "you", "today?"],
        "artery" => vec!["Processing.", "Request", "acknowledged.", "Awaiting", "parameters."],
        _ => vec!["Streaming", "response", "in", "progress", "..."],
    }
    .into_iter()
    .map(|s| s.to_string())
    .collect();

    let stream = stream::iter(words).map(|word| {
        Ok(Event::default()
            .data(word)
            .event("message"))
    });

    Sse::new(stream).keep_alive(
        axum::response::sse::KeepAlive::new()
            .interval(std::time::Duration::from_secs(15))
            .text("keep-alive"),
    )
}
