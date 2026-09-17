"""Event-driven publish path: Azure Event Hubs with a Kafka-compatible mode.

Event Hubs exposes a native AMQP producer (`azure-eventhub`) and a
Kafka-protocol endpoint on port 9093, which is why WES can standardize
on Event Hubs as the backbone while still speaking the Kafka wire
protocol to interoperate with existing Kafka consumers/tooling during
the AWS -> Azure migration window. This module offers both producers
behind one interface so callers never branch on transport.
"""
from __future__ import annotations

import json
from typing import Protocol

from app.core.telemetry import get_logger
from app.models.workstream import WorkstreamEvent

logger = get_logger(__name__)


class EventPublisher(Protocol):
    """Publishes a `WorkstreamEvent` to the streaming backbone."""

    async def publish(self, event: WorkstreamEvent) -> None:
        ...


class EventHubPublisher:
    """Publishes via the native Azure Event Hubs AMQP producer client.

    Lazily imports the Azure SDK so the showcase runs without an Event
    Hubs namespace configured (falls back to `InMemoryPublisher` in
    `get_publisher` below).
    """

    def __init__(self, connection_str: str, eventhub_name: str) -> None:
        self._connection_str = connection_str
        self._eventhub_name = eventhub_name

    async def publish(self, event: WorkstreamEvent) -> None:
        from azure.eventhub.aio import EventHubProducerClient
        from azure.eventhub import EventData

        async with EventHubProducerClient.from_connection_string(
            conn_str=self._connection_str, eventhub_name=self._eventhub_name
        ) as producer:
            batch = await producer.create_batch()
            batch.add(EventData(event.model_dump_json()))
            await producer.send_batch(batch)
        logger.info("eventhub.published", event_type=event.event_type, workstream_id=event.workstream.id)


class KafkaCompatiblePublisher:
    """Publishes to Event Hubs' Kafka-compatible endpoint via aiokafka.

    Demonstrates that Kafka-native consumers (e.g. legacy services not
    yet migrated off Node.js/Express tooling) can keep working unchanged
    against the same Event Hubs namespace, satisfying the JD's
    "Kafka compatible messaging patterns" requirement without running a
    separate Kafka cluster.
    """

    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._producer = None

    async def _get_producer(self):
        if self._producer is None:
            from aiokafka import AIOKafkaProducer

            self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap_servers)
            await self._producer.start()
        return self._producer

    async def publish(self, event: WorkstreamEvent) -> None:
        producer = await self._get_producer()
        await producer.send_and_wait(self._topic, event.model_dump_json().encode())
        logger.info("kafka.published", event_type=event.event_type, workstream_id=event.workstream.id)


class InMemoryPublisher:
    """No-infra fallback publisher for local dev/demo/tests.

    Buffers events and fans them out to registered async subscribers
    (used to bridge into the SignalR broadcast path in this showcase).
    """

    def __init__(self) -> None:
        self.published: list[WorkstreamEvent] = []
        self._subscribers: list = []

    def subscribe(self, callback) -> None:
        self._subscribers.append(callback)

    async def publish(self, event: WorkstreamEvent) -> None:
        self.published.append(event)
        logger.info("inmemory.published", event_type=event.event_type, workstream_id=event.workstream.id)
        for callback in self._subscribers:
            await callback(event)


_in_memory_singleton = InMemoryPublisher()


def get_publisher(settings) -> EventPublisher:
    """Select a publisher implementation based on configured settings.

    Falls back to the in-memory publisher (wired to the SignalR hub) when
    no Event Hubs connection string is configured, so `make run` works
    with zero cloud dependencies.
    """
    if settings.eventhub_connection_str:
        return EventHubPublisher(settings.eventhub_connection_str, settings.eventhub_name)
    return _in_memory_singleton
