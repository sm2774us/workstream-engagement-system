/**
 * Subscribes to live Workstream mutations. Transport-agnostic: works
 * identically whether the backend negotiate response points at the
 * local WebSocket hub or a real Azure SignalR Service endpoint, because
 * both emit the same `{target, arguments}` envelope.
 */
import { useEffect, useRef, useState } from "react";
import type { WorkstreamEvent } from "../types";

export function useRealtimeWorkstreams(onEvent: (event: WorkstreamEvent) => void) {
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function connect() {
      const negotiateResp = await fetch("/api/v1/realtime/negotiate");
      const negotiate = await negotiateResp.json();
      if (cancelled) return;

      const wsUrl =
        negotiate.mode === "local-websocket"
          ? `ws://${window.location.hostname}:8000/api/v1/realtime/ws`
          : negotiate.url; // real Azure SignalR endpoint

      const socket = new WebSocket(wsUrl);
      socket.onopen = () => setConnected(true);
      socket.onclose = () => setConnected(false);
      socket.onmessage = (msg) => {
        const envelope = JSON.parse(msg.data);
        if (envelope.target === "workstreamUpdated") {
          onEvent(envelope.arguments[0] as WorkstreamEvent);
        }
      };
      socketRef.current = socket;
    }

    connect();
    return () => {
      cancelled = true;
      socketRef.current?.close();
    };
  }, [onEvent]);

  return { connected };
}
