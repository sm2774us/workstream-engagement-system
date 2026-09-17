//! Axum HTTP surface: exposes the same risk engine over plain HTTP/JSON
//! for tooling that doesn't speak gRPC (curl, browser devtools, non-gRPC
//! legacy services still mid-migration), satisfying the JD's explicit
//! mention of Axum alongside Tonic rather than choosing just one.
use axum::{routing::{get, post}, Json, Router};
use serde::{Deserialize, Serialize};
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;

use crate::risk::score_workstream;

#[derive(Deserialize)]
pub struct ScoreRequest {
    pub title: String,
    pub status: String,
}

#[derive(Serialize)]
pub struct ScoreResponse {
    pub score: f64,
    pub engine: &'static str,
}

async fn healthz() -> Json<serde_json::Value> {
    Json(serde_json::json!({"status": "ok", "service": "wes-risk-engine"}))
}

async fn score(Json(req): Json<ScoreRequest>) -> Json<ScoreResponse> {
    Json(ScoreResponse {
        score: score_workstream(&req.title, &req.status),
        engine: "rust-axum",
    })
}

/// Build the Axum router. Split from `main.rs` so it's independently
/// testable via `axum::Router::oneshot` in integration tests.
pub fn build_router() -> Router {
    Router::new()
        .route("/healthz", get(healthz))
        .route("/score", post(score))
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http())
}
