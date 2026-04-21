//! logging.rs – Request logging middleware

use axum::extract::Request;
use axum::middleware::Next;
use axum::response::Response;
use std::time::Instant;
use tracing::{info, warn};

pub async fn log_request(
    req: Request,
    next: Next,
) -> Response {
    let method = req.method().clone();
    let uri = req.uri().clone();
    let start = Instant::now();

    let response = next.run(req).await;

    let duration = start.elapsed();
    let status = response.status();

    if status.is_success() {
        info!(
            "{} {} -> {} ({:.2?})",
            method,
            uri.path(),
            status.as_u16(),
            duration
        );
    } else {
        warn!(
            "{} {} -> {} ({:.2?})",
            method,
            uri.path(),
            status.as_u16(),
            duration
        );
    }

    response
}
