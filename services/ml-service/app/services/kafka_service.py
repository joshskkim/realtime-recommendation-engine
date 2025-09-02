"""
Kafka service for event streaming (async version)
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class KafkaService:
    """Kafka service for publishing events asynchronously"""

    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
        self.client_id = os.getenv("KAFKA_CLIENT_ID", "ml-service")
        self.producer: Optional[AIOKafkaProducer] = None

        self.topics = {
            "user_interactions": os.getenv("KAFKA_TOPIC_USER_INTERACTIONS", "user-interactions"),
            "recommendations": os.getenv("KAFKA_TOPIC_RECOMMENDATIONS", "recommendations-generated"),
            "model_updates": os.getenv("KAFKA_TOPIC_MODEL_UPDATES", "model-updates"),
            "system_events": os.getenv("KAFKA_TOPIC_SYSTEM_EVENTS", "system-events")
        }

    async def start(self):
        """Initialize Kafka producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=f"{self.client_id}-producer",
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8') if k else None
            )
            await self.producer.start()
            logger.info("✅ Kafka producer started")

            await self.publish_system_event({
                "event": "ml_service_started",
                "timestamp": datetime.now().isoformat(),
                "service": "ml-service"
            })

        except Exception as e:
            logger.error(f"❌ Kafka producer initialization failed: {e}")
            self.producer = None

    async def publish_event(self, topic: str, value: Dict[str, Any], key: Optional[str] = None):
        if not self.producer:
            logger.warning("Kafka producer not available")
            return
        try:
            await self.producer.send_and_wait(topic, value=value, key=key.encode('utf-8') if key else None)
            logger.debug(f"Published event to {topic}")
        except Exception as e:
            logger.error(f"Error publishing to {topic}: {e}")

    async def publish_interaction(self, interaction_data: Dict[str, Any]):
        await self.publish_event(
            self.topics["user_interactions"],
            interaction_data,
            key=str(interaction_data.get("user_id"))
        )

    async def publish_recommendation_event(self, recommendation_data: Dict[str, Any]):
        await self.publish_event(
            self.topics["recommendations"],
            recommendation_data,
            key=str(recommendation_data.get("user_id"))
        )

    async def publish_model_update(self, model_data: Dict[str, Any]):
        await self.publish_event(self.topics["model_updates"], model_data)

    async def publish_system_event(self, system_data: Dict[str, Any]):
        await self.publish_event(self.topics["system_events"], system_data)

    async def close(self):
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer closed")


class KafkaConsumerService:
    """Async Kafka consumer service"""

    def __init__(self, recommendation_service=None):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
        self.group_id = os.getenv("KAFKA_GROUP_ID", "ml-service-consumers")
        self.recommendation_service = recommendation_service
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        self.consumer_task: Optional[asyncio.Task] = None

    async def start_consuming(self):
        try:
            self.consumer = AIOKafkaConsumer(
                'user-interactions',
                'model-updates',
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            await self.consumer.start()
            self.running = True
            logger.info("✅ Kafka consumer started")

            self.consumer_task = asyncio.create_task(self._consume_messages())

        except Exception as e:
            logger.error(f"❌ Failed to start Kafka consumer: {e}")

    async def _consume_messages(self):
        try:
            while self.running:
                async for message in self.consumer:
                    await self._process_message(message.topic, message.value)
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
            await asyncio.sleep(5)

    async def _process_message(self, topic: str, message: Dict[str, Any]):
        try:
            if topic == 'user-interactions':
                await self._handle_interaction_event(message)
            elif topic == 'model-updates':
                await self._handle_model_update_event(message)
        except Exception as e:
            logger.error(f"Error processing message from {topic}: {e}")

    async def _handle_interaction_event(self, message: Dict[str, Any]):
        logger.debug(f"Processed interaction: {message.get('user_id')} -> {message.get('item_id')}")

    async def _handle_model_update_event(self, message: Dict[str, Any]):
        logger.info(f"Received model update event: {message}")
        if self.recommendation_service:
            await self.recommendation_service.train_models()

    async def stop(self):
        self.running = False
        if self.consumer_task:
            self.consumer_task.cancel()
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")
