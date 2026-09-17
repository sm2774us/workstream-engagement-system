//! Compiles `proto/risk.proto` into Rust (server) and Python (client) stubs
//! at build time via `tonic-build`, keeping the gRPC contract as the single
//! source of truth for both the Rust engine and the FastAPI client.
fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure()
        .build_server(true)
        .build_client(false)
        .compile_protos(&["proto/risk.proto"], &["proto"])?;
    Ok(())
}
