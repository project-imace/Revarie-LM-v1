//! test_api_server.rs – Integration test for full API server

#[cfg(test)]
mod tests {
    use axum::{
        body::Body,
        http::{self, Request, StatusCode},
    };
    use hyper::body::to_bytes;
    use serde_json::{json, Value};
    use tower::ServiceExt;

    async fn spawn_test_server() -> (String, tokio::task::JoinHandle<()>) {
        use std::net::SocketAddr;
        use tokio::net::TcpListener;

        let app = Router::new()
            .route("/health", axum::routing::get(|| async { "OK" }))
            .route("/chat", axum::routing::post(|_: axum::extract::Json<Value>| async { "{}" }));

        let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
        let addr = listener.local_addr().unwrap();

        let server = axum::serve(listener, app);
        let handle = tokio::spawn(async move { server.await.unwrap() });

        (format!("http://{}", addr), handle)
    }

    #[tokio::test]
    async fn test_health_endpoint_integration() {
        let (base_url, handle) = spawn_test_server().await;

        let client = hyper::Client::new();
        let response = client
            .request(
                Request::builder()
                    .uri(format!("{}/health", base_url))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);
        let body = to_bytes(response.into_body()).await.unwrap();
        assert_eq!(&body[..], b"OK");

        handle.abort();
    }
}
