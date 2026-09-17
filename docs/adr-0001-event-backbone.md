# ADR-0001: Azure Event Hubs as the sole event backbone (Kafka-compatible mode)

**Status:** Accepted

## Context
WES needs an event-driven backbone for Workstream mutations. Legacy
services speak the Kafka wire protocol; the target Azure landing zone
standardizes on Azure-native PaaS.

## Decision
Adopt Azure Event Hubs as the single physical backbone. Publish via the
native AMQP SDK from new Python services; expose the Kafka-compatible
endpoint (port 9093) for legacy/Kafka-native consumers during migration.

## Consequences
- One operational surface (Event Hubs namespace) instead of running a
  parallel Kafka cluster.
- Legacy consumers migrate on their own timeline without a hard cutover.
- Schema evolution is enforced at the `WorkstreamEvent` Pydantic model,
  not the transport.
