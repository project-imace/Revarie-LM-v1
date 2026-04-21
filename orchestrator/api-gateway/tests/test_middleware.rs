//! test_middleware.rs – Middleware unit tests

#[cfg(test)]
mod tests {
    use axum::{
        body::Body,
        http::{Request, StatusCode},
        middleware,
        response::Response,
        routing::get,
        Router,
    };
    use tower::ServiceExt;

    async fn auth_middleware(req: Request, next: middleware::Next) -> Result<Response, StatusCode> {
        if req.headers().contains_key("x-test-auth") {
            Ok(next.run(req).await)
        } else {
            Err(StatusCode::UNAUTHORIZED)
        }
    }

    async fn test_handler() -> &'static str {
        "ok"
    }

    #[tokio::test]
    async fn test_auth_middleware_allows_valid_header() {
        let app = Router::new()
            .route("/test", get(test_handler))
            .layer(middleware::from_fn(auth_middleware));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/test")
                    .header("x-test-auth", "valid")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);
    }

    #[tokio::test]
    async fn test_auth_middleware_blocks_missing_header() {
        let app = Router::new()
            .route("/test", get(test_handler))
            .layer(middleware::from_fn(auth_middleware));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/test")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
    }
}
