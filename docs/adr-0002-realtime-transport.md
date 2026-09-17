# ADR-0002: Azure SignalR Service (serverless mode) for real-time fan-out

**Status:** Accepted

## Context
Workstream board clients need sub-second update propagation without the
API tier owning persistent socket state (which complicates horizontal
scaling on AKS).

## Decision
Use Azure SignalR Service in serverless mode: the API POSTs to the
SignalR management REST API; SignalR owns client connections directly.
A local WebSocket hub implementing the same `RealtimeBroadcaster`
interface stands in for local dev/demo.

## Consequences
- API pods stay stateless; horizontal scaling is trivial.
- Local dev requires no Azure subscription.
- Client code is transport-agnostic (same message envelope both ways).
