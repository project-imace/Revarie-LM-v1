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

#[derive(Debug, Deserialize)]
pub struct ChatRequest {
    pub participant_id: String,
    pub message: String,
    pub persona: Option<String>, // "samara" or "artery", defaults from study group if omitted
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
    info!(
        "Chat request from participant {} (persona: {:?})",
        payload.participant_id, payload.persona
    );

    // Simulate processing – in production this would call the orchestrator
    let persona = payload.persona.unwrap_or_else(|| "samara".to_string());
    let response_text = match persona.as_str() {
        "samara" => format!("Hello! I'm Samara. You said: '{}'. How are you feeling today?", payload.message),
        "artery" => format!("Input received. Processing: '{}'. Awaiting further instructions.", payload.message),
        _ => format!("Message processed: '{}'", payload.message),
    };

    let response = ChatResponse {
        response: response_text,
        persona,
        session_id: payload.session_id.unwrap_or_else(|| uuid::Uuid::new_v4().to_string()),
        usage: Some(UsageStats {
            prompt_tokens: payload.message.len() as u32 / 4,
            completion_tokens: response_text.len() as u32 / 4,
            total_tokens: (payload.message.len() + response_text.len()) as u32 / 4,
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
