"""
Kafka service for event streaming
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class KafkaService:
    """Kafka service for publishing and consuming events"""
    
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
        self.client_id = os.getenv("KAFKA_CLIENT_ID", "ml-service")
        self.producer = None
        self.consumer = None
        
        # Topic names
        self.topics = {
            "user_interactions": os.getenv("KAFKA_TOPIC_USER_INTERACTIONS", "user-interactions"),
            "recommendations": os.getenv("KAFKA_TOPIC_RECOMMENDATIONS", "recommendations-generated"),
            "model_updates": os.getenv("KAFKA_TOPIC_MODEL_UPDATES", "model-updates"),
            "system_events": os.getenv("KAFKA_TOPIC_SYSTEM_EVENTS", "system-events")
        }
    
    async def start(self):
        """Initialize Kafka connections"""
        try:
            # Initialize producer
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=f"{self.client_id}-producer",
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8') if k else None,
                retries=3,
                max_in_flight_requests_per_connection=1,
                acks='all'
            )
            
            logger.info("✅ Kafka producer initialized")
            
            # Test connection by sending a test message
            await self.publish_system_event({
                "event": "ml_service_started",
                "timestamp": datetime.now().isoformat(),
                "service": "ml-service"
            })
            
        except Exception as e:
            logger.error(f"❌ Kafka initialization failed: {e}")
            self.producer = None
    
    async def publish_interaction(self, interaction_data: Dict[str, Any]):
        """Publish user interaction event"""
        if not self.producer:
            logger.warning("Kafka producer not available")
            return
        
        try:
            future = self.producer.send(
                self.topics["user_interactions"],
                value=interaction_data,
                key=str(interaction_data.get("user_id"))
            )
            
            # Don't block, but log if send fails
            future.add_callback(self._on_send_success)
            future.add_errback(self._on_send_error)
            
        except Exception as e:
            logger.error(f"Error publishing interaction: {e}")
    
    async def publish_recommendation_event(self, recommendation_data: Dict[str, Any]):
        """Publish recommendation generation event"""
        if not self.producer:
            logger.warning("Kafka producer not available")
            return
        
        try:
            future = self.producer.send(
                self.topics["recommendations"],
                value=recommendation_data,
                key=str(recommendation_data.get("user_id"))
            )
            
            future.add_callback(self._on_send_success)
            future.add_errback(self._on_send_error)
            
        except Exception as e:
            logger.error(f"Error publishing recommendation event: {e}")
    
    async def publish_model_update(self, model_data: Dict[str, Any]):
        """Publish model update event"""
        if not self.producer:
            logger.warning("Kafka producer not available")
            return
        
        try:
            future = self.producer.send(
                self.topics["model_updates"],
                value=model_data
            )
            
            future.add_callback(self._on_send_success)
            future.add_errback(self._on_send_error)
            
        except Exception as e:
            logger.error(f"Error publishing model update: {e}")
    
    async def publish_system_event(self, system_data: Dict[str, Any]):
        """Publish system event"""
        if not self.producer:
            logger.warning("Kafka producer not available")
            return
        
        try:
            future = self.producer.send(
                self.topics["system_events"],
                value=system_data
            )
            
            future.add_callback(self._on_send_success)
            future.add_errback(self._on_send_error)
            
        except Exception as e:
            logger.error(f"Error publishing system event: {e}")
    
    def _on_send_success(self, record_metadata):
        """Callback for successful message send"""
        logger.debug(f"Message sent to {record_metadata.topic} partition {record_metadata.partition}")
    
    def _on_send_error(self, excp):
        """Callback for failed message send"""
        logger.error(f"Failed to send message: {excp}")
    
    def close(self):
        """Close Kafka connections"""
        try:
            if self.producer:
                self.producer.close()
            if self.consumer:
                self.consumer.close()
            logger.info("Kafka connections closed")
        except Exception as e:
            logger.error(f"Error closing Kafka connections: {e}")


class KafkaConsumerService:
    """Separate service for consuming Kafka messages"""
    
    def __init__(self, recommendation_service=None):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
        self.group_id = os.getenv("KAFKA_GROUP_ID", "ml-service-consumers")
        self.recommendation_service = recommendation_service
        self.consumer = None
        self.running = False
    
    async def start_consuming(self):
        """Start consuming messages from Kafka topics"""
        try:
            self.consumer = KafkaConsumer(
                'user-interactions',
                'model-updates',
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
            self.running = True
            logger.info("✅ Started Kafka consumer")
            
            # Start consuming in background
            asyncio.create_task(self._consume_messages())
            
        except Exception as e:
            logger.error(f"❌ Failed to start Kafka consumer: {e}")
    
    async def _consume_messages(self):
        """Consume messages from Kafka"""
        while self.running:
            try:
                message_batch = self.consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        await self._process_message(message.topic, message.value)
                
            except Exception as e:
                logger.error(f"Error consuming messages: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _process_message(self, topic: str, message: Dict[str, Any]):
        """Process individual message based on topic"""
        try:
            if topic == 'user-interactions':
                await self._handle_interaction_event(message)
            elif topic == 'model-updates':
                await self._handle_model_update_event(message)
            
        except Exception as e:
            logger.error(f"Error processing message from {topic}: {e}")
    
    async def _handle_interaction_event(self, message: Dict[str, Any]):
        """Handle user interaction event"""
        # Update real-time user profiles or trigger model updates
        logger.debug(f"Processed interaction: {message.get('user_id')} -> {message.get('item_id')}")
        
        # Could trigger incremental model updates here
        # For now, just log the event
    
    async def _handle_model_update_event(self, message: Dict[str, Any]):
        """Handle model update event"""
        logger.info(f"Received model update event: {message}")
        
        # Could trigger model retraining here
        if self.recommendation_service:
            await self.recommendation_service.train_models()
    
    def stop(self):
        """Stop consuming messages"""
        self.running = False
        if self.consumer:
            self.consumer.close()