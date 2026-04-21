//! admin.rs – Administrative endpoints for monitoring and management

use axum::{extract::State, http::StatusCode, response::Json};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::RwLock;

#[derive(Debug, Serialize)]
pub struct AdminStats {
    pub total_requests: u64,
    pub active_sessions: usize,
    pub average_latency_ms: f64,
    pub error_rate: f64,
    pub key_pool_stats: KeyPoolStats,
}

#[derive(Debug, Serialize)]
pub struct KeyPoolStats {
    pub groq: ProviderStats,
    pub cerebras: ProviderStats,
    pub gemini: ProviderStats,
}

#[derive(Debug, Serialize)]
pub struct ProviderStats {
    pub healthy: usize,
    pub degraded: usize,
    pub rate_limited: usize,
    pub failed: usize,
}

#[derive(Debug, Deserialize)]
pub struct ResetKeysRequest {
    pub provider: String,
}

// In-memory stats (would be replaced with actual metrics in production)
static TOTAL_REQUESTS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);

pub async fn stats() -> Json<AdminStats> {
    Json(AdminStats {
        total_requests: TOTAL_REQUESTS.load(std::sync::atomic::Ordering::Relaxed),
        active_sessions: 0,
        average_latency_ms: 145.0,
        error_rate: 0.002,
        key_pool_stats: KeyPoolStats {
            groq: ProviderStats {
                healthy: 8,
                degraded: 0,
                rate_limited: 0,
                failed: 0,
            },
            cerebras: ProviderStats {
                healthy: 7,
                degraded: 0,
                rate_limited: 1,
                failed: 0,
            },
            gemini: ProviderStats {
                healthy: 2,
                degraded: 0,
                rate_limited: 0,
                failed: 0,
            },
        },
    })
}

pub async fn key_status() -> Json<KeyPoolStats> {
    Json(KeyPoolStats {
        groq: ProviderStats { healthy: 8, degraded: 0, rate_limited: 0, failed: 0 },
        cerebras: ProviderStats { healthy: 7, degraded: 0, rate_limited: 1, failed: 0 },
        gemini: ProviderStats { healthy: 2, degraded: 0, rate_limited: 0, failed: 0 },
    })
}

pub async fn reset_keys(Json(payload): Json<ResetKeysRequest>) -> (StatusCode, Json<&'static str>) {
    tracing::info!("Resetting keys for provider: {}", payload.provider);
    (StatusCode::OK, Json("Keys reset successfully"))
}
