//! main.rs – Revarie API Gateway (Axum Server)
//!
//! Primary HTTP server for the Revarie LM v1.0 cognitive architecture.
//! Routes chat requests to the appropriate persona, handles health checks,
//! and provides administrative endpoints for monitoring.

use axum::{
    extract::Request,
    http::{header, Method, StatusCode},
    response::{IntoResponse, Response},
    routing::{get, post},
    Router,
};
use std::net::SocketAddr;
use tower::ServiceBuilder;
use tower_http::{
    cors::{Any, CorsLayer},
    trace::{DefaultMakeSpan, DefaultOnRequest, DefaultOnResponse, TraceLayer},
};
use tracing::{info, Level};

mod routes;
mod middleware;

use middleware::{auth::auth_middleware, logging::log_request};
use routes::{admin, chat, health};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "revarie_api_gateway=info,tower_http=debug".into()),
        )
        .init();

    info!("Starting Revarie API Gateway v1.0.0");

    // CORS configuration (allow frontend origins)
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods([Method::GET, Method::POST, Method::OPTIONS])
        .allow_headers([header::CONTENT_TYPE, header::AUTHORIZATION]);

    // Trace layer for request logging
    let trace = TraceLayer::new_for_http()
        .make_span_with(DefaultMakeSpan::new().level(Level::INFO))
        .on_request(DefaultOnRequest::new().level(Level::INFO))
        .on_response(DefaultOnResponse::new().level(Level::INFO));

    // Middleware stack
    let middleware_stack = ServiceBuilder::new()
        .layer(trace)
        .layer(cors)
        .layer(axum::middleware::from_fn(log_request))
        .layer(axum::middleware::from_fn(auth_middleware));

    // Build router
    let app = Router::new()
        .route("/health", get(health::health_check))
        .route("/health/detailed", get(health::detailed_health))
        .route("/chat", post(chat::chat_handler))
        .route("/chat/stream", post(chat::chat_stream_handler))
        .route("/admin/stats", get(admin::stats))
        .route("/admin/keys", get(admin::key_status))
        .route("/admin/keys/reset", post(admin::reset_keys))
        .layer(middleware_stack)
        .fallback(handler_404);

    let addr = SocketAddr::from(([0, 0, 0, 0], 3000));
    info!("Listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}

async fn handler_404() -> impl IntoResponse {
    (StatusCode::NOT_FOUND, "The requested resource was not found.")
}
