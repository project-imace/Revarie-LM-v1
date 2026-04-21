//! health.rs – Health check endpoints

use axum::{extract::State, http::StatusCode, response::Json};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::RwLock;

#[derive(Debug, Serialize, Deserialize)]
pub struct HealthStatus {
    pub status: String,
    pub version: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DetailedHealthStatus {
    pub status: String,
    pub version: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub components: ComponentHealth,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ComponentHealth {
    pub api_gateway: String,
    pub key_vault: String,
    pub model_router: String,
    pub providers: ProviderHealth,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProviderHealth {
    pub groq: String,
    pub cerebras: String,
    pub gemini: String,
}

pub async fn health_check() -> Json<HealthStatus> {
    Json(HealthStatus {
        status: "healthy".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        timestamp: chrono::Utc::now(),
    })
}

pub async fn detailed_health() -> Json<DetailedHealthStatus> {
    Json(DetailedHealthStatus {
        status: "healthy".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        timestamp: chrono::Utc::now(),
        components: ComponentHealth {
            api_gateway: "operational".to_string(),
            key_vault: "operational".to_string(),
            model_router: "operational".to_string(),
            providers: ProviderHealth {
                groq: "available".to_string(),
                cerebras: "available".to_string(),
                gemini: "available".to_string(),
            },
        },
    })
}
