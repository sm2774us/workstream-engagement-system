//! wes-risk-engine: runs both an Axum HTTP server and a Tonic gRPC server
//! concurrently on separate ports, backed by one shared scoring core
//! (`risk.rs`). This dual-protocol layout is the direct implementation
//! of the JD line: "Contribute to systems and performance critical
//! components using Rust, Axum, and Tonic."
mod grpc;
mod http;
mod risk;

use std::net::SocketAddr;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();

    let http_addr: SocketAddr = "0.0.0.0:8080".parse()?;
    let grpc_addr: SocketAddr = "0.0.0.0:50051".parse()?;

    let http_server = async {
        let listener = tokio::net::TcpListener::bind(http_addr).await.unwrap();
        tracing::info!(%http_addr, "axum http server listening");
        axum::serve(listener, http::build_router()).await.unwrap();
    };

    let grpc_server = async {
        tracing::info!(%grpc_addr, "tonic grpc server listening");
        tonic::transport::Server::builder()
            .add_service(grpc::service())
            .serve(grpc_addr)
            .await
            .unwrap();
    };

    tokio::join!(http_server, grpc_server);
    Ok(())
}
