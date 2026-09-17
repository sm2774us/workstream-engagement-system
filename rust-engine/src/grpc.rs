//! Tonic gRPC service implementation, backing the FastAPI `RustEngineClient`.
use tonic::{Request, Response, Status};

use crate::risk::score_workstream;

pub mod risk_proto {
    tonic::include_proto!("risk");
}

use risk_proto::risk_engine_server::{RiskEngine, RiskEngineServer};
use risk_proto::{ScoreRequest, ScoreResponse};

#[derive(Default)]
pub struct RiskEngineService;

#[tonic::async_trait]
impl RiskEngine for RiskEngineService {
    async fn score_workstream(
        &self,
        request: Request<ScoreRequest>,
    ) -> Result<Response<ScoreResponse>, Status> {
        let req = request.into_inner();
        let score = score_workstream(&req.title, &req.status);
        Ok(Response::new(ScoreResponse { score, engine: "rust-tonic".into() }))
    }
}

pub fn service() -> RiskEngineServer<RiskEngineService> {
    RiskEngineServer::new(RiskEngineService)
}
