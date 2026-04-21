//! auth.rs – Authentication middleware

use axum::extract::Request;
use axum::middleware::Next;
use axum::response::{Response, IntoResponse};
use axum::http::{header, StatusCode};
use tracing::warn;

pub async fn auth_middleware(
    req: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    // Skip auth for health endpoints
    if req.uri().path().starts_with("/health") {
        return Ok(next.run(req).await);
    }

    // Skip auth for OPTIONS (CORS preflight)
    if req.method() == "OPTIONS" {
        return Ok(next.run(req).await);
    }

    // Check for API key in Authorization header
    let auth_header = req
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|h| h.to_str().ok());

    match auth_header {
        Some(token) if token.starts_with("Bearer ") => {
            let api_key = &token[7..];
            // In production, validate against a secure store
            if validate_api_key(api_key).await {
                Ok(next.run(req).await)
            } else {
                warn!("Invalid API key: {}", api_key);
                Err(StatusCode::UNAUTHORIZED)
            }
        }
        Some(_) => {
            warn!("Malformed Authorization header");
            Err(StatusCode::UNAUTHORIZED)
        }
        None => {
            warn!("Missing Authorization header");
            Err(StatusCode::UNAUTHORIZED)
        }
    }
}

async fn validate_api_key(key: &str) -> bool {
    // Placeholder – replace with actual validation
    !key.is_empty() && key.len() >= 32
}
