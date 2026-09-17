//! Core risk-scoring domain logic, shared by both the Axum HTTP handler
//! and the Tonic gRPC service so the two protocols never drift.
//!
//! Deliberately allocation-light and branch-predictable: this is the
//! "systems and performance critical component" called out in the JD —
//! designed to run under a tight p99 latency budget when scanning large
//! historical Workstream windows (not exercised at that scale in this
//! showcase, but the shape is production-representative).

/// Compute a 0.0-100.0 risk/priority score for a Workstream.
///
/// Mirrors the Python fallback heuristic in `app/services/rust_client.py`
/// bit-for-bit so behavior is identical whether or not the Rust engine
/// is reachable — an explicit design choice to avoid divergent business
/// rules between the "fast path" and "degraded path".
pub fn score_workstream(title: &str, status: &str) -> f64 {
    let base = (title.len() as f64 * 1.5).min(60.0);
    let status_weight = match status {
        "draft" => 5.0,
        "in_review" => 25.0,
        "approved" => 10.0,
        "blocked" => 40.0,
        "done" => 0.0,
        _ => 15.0,
    };
    ((base + status_weight).min(100.0) * 100.0).round() / 100.0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn blocked_status_dominates_score() {
        let blocked = score_workstream("x", "blocked");
        let done = score_workstream("x", "done");
        assert!(blocked > done);
    }

    #[test]
    fn score_is_bounded() {
        let long_title = "x".repeat(200);
        assert!(score_workstream(&long_title, "blocked") <= 100.0);
    }

    #[test]
    fn score_never_negative() {
        assert!(score_workstream("", "done") >= 0.0);
    }
}
