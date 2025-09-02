"""
Kafka Streams Processor for Real-time Recommendation Engine
Handles real-time event processing and streaming analytics
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from confluent_kafka import Consumer, Producer, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic
import redis
import numpy as np
from collections import defaultdict, Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UserInteraction:
    """User interaction event"""
    user_id: str
    item_id: str
    interaction_type: str
    rating: Optional[float]
    timestamp: str
    session_id: Optional[str]
    metadata: Optional[Dict]


@dataclass
class RecommendationEvent:
    """Recommendation generated event"""
    user_id: str
    recommendations: List[str]
    strategy: str
    score: float
    timestamp: str
    metadata: Optional[Dict]


class StreamProcessor:
    """Main Kafka Streams processor for real-time analytics"""
    
    def __init__(self):
        self.producer = Producer({
            'bootstrap.servers': os.getenv('KAFKA_BROKERS', 'kafka:29092'),
            'client.id': 'stream-processor',
            'linger.ms': 10,
            'batch.size': 32768,
            'compression.type': 'snappy'
        })
        
        self.consumer = Consumer({
            'bootstrap.servers': os.getenv('KAFKA_BROKERS', 'kafka:29092'),
            'group.id': 'stream-processor-group',
            'auto.offset.reset': 'latest',
            'enable.auto.commit': True,
            'session.timeout.ms': 30000,
            'max.poll.interval.ms': 600000
        })
        
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        # Stream processing state
        self.user_sessions = defaultdict(list)
        self.item_popularity = Counter()
        self.user_profiles = {}
        self.trending_window = []
        
        # Initialize topics
        self._ensure_topics()
        
    def _ensure_topics(self):
        """Ensure required Kafka topics exist"""
        admin = AdminClient({'bootstrap.servers': os.getenv('KAFKA_BROKERS', 'kafka:29092')})
        
        topics = [
            NewTopic('user-interactions', num_partitions=3, replication_factor=1),
            NewTopic('recommendations-generated', num_partitions=3, replication_factor=1),
            NewTopic('trending-items', num_partitions=1, replication_factor=1),
            NewTopic('user-profiles-updated', num_partitions=3, replication_factor=1),
            NewTopic('ab-test-events', num_partitions=1, replication_factor=1),
        ]
        
        fs = admin.create_topics(topics, request_timeout=15.0)
        for topic, f in fs.items():
            try:
                f.result()
                logger.info(f"Topic {topic} created")
            except Exception as e:
                logger.debug(f"Topic {topic} already exists: {e}")
    
    def process_interaction(self, interaction: UserInteraction):
        """Process individual user interaction"""
        # Update user session
        self.user_sessions[interaction.user_id].append({
            'item_id': interaction.item_id,
            'timestamp': interaction.timestamp,
            'type': interaction.interaction_type
        })
        
        # Update item popularity
        self.item_popularity[interaction.item_id] += 1
        
        # Update user profile
        self._update_user_profile(interaction)
        
        # Check for real-time triggers
        if self._should_trigger_recommendation(interaction):
            self._generate_real_time_recommendation(interaction.user_id)
        
        # Update trending items window
        self._update_trending_window(interaction)
        
    def _update_user_profile(self, interaction: UserInteraction):
        """Update user profile based on interaction"""
        user_id = interaction.user_id
        
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'interaction_count': 0,
                'avg_rating': 0,
                'categories': Counter(),
                'recent_items': [],
                'last_active': interaction.timestamp
            }
        
        profile = self.user_profiles[user_id]
        profile['interaction_count'] += 1
        profile['last_active'] = interaction.timestamp
        
        # Update recent items (keep last 20)
        profile['recent_items'].append(interaction.item_id)
        if len(profile['recent_items']) > 20:
            profile['recent_items'].pop(0)
        
        # Update average rating if provided
        if interaction.rating:
            current_avg = profile['avg_rating']
            count = profile['interaction_count']
            profile['avg_rating'] = ((current_avg * (count - 1)) + interaction.rating) / count
        
        # Store in Redis
        self.redis_client.setex(
            f"user_profile:{user_id}",
            3600,
            json.dumps(profile)
        )
        
        # Emit profile update event
        self.producer.produce(
            'user-profiles-updated',
            json.dumps({
                'user_id': user_id,
                'profile': profile,
                'timestamp': interaction.timestamp
            })
        )
    
    def _should_trigger_recommendation(self, interaction: UserInteraction) -> bool:
        """Determine if real-time recommendation should be triggered"""
        # Trigger on specific events
        if interaction.interaction_type in ['purchase', 'add_to_cart']:
            return True
        
        # Trigger after N interactions in session
        session_interactions = len(self.user_sessions[interaction.user_id])
        if session_interactions % 5 == 0:  # Every 5 interactions
            return True
        
        return False
    
    def _generate_real_time_recommendation(self, user_id: str):
        """Generate real-time recommendation for user"""
        # Get user's recent items
        recent_items = self.user_profiles.get(user_id, {}).get('recent_items', [])
        
        # Simple collaborative filtering based on co-occurrence
        recommendations = self._get_cooccurrence_recommendations(recent_items)
        
        # Emit recommendation event
        event = RecommendationEvent(
            user_id=user_id,
            recommendations=recommendations[:10],
            strategy='real-time-collaborative',
            score=0.85,
            timestamp=datetime.utcnow().isoformat(),
            metadata={'trigger': 'real-time-stream'}
        )
        
        self.producer.produce(
            'recommendations-generated',
            json.dumps(asdict(event))
        )
        
        # Cache recommendations
        self.redis_client.setex(
            f"rt_recommendations:{user_id}",
            300,  # 5 minutes
            json.dumps(recommendations)
        )
    
    def _get_cooccurrence_recommendations(self, items: List[str]) -> List[str]:
        """Get recommendations based on item co-occurrence"""
        cooccurrence_scores = Counter()
        
        for item in items[-5:]:  # Consider last 5 items
            # Get users who interacted with this item
            similar_users = self._get_users_by_item(item)
            
            # Get items those users also interacted with
            for user in similar_users[:100]:  # Limit to 100 users
                user_items = self.user_profiles.get(user, {}).get('recent_items', [])
                for user_item in user_items:
                    if user_item not in items:
                        cooccurrence_scores[user_item] += 1
        
        # Return top items
        return [item for item, _ in cooccurrence_scores.most_common(20)]
    
    def _get_users_by_item(self, item_id: str) -> List[str]:
        """Get users who interacted with an item"""
        users = []
        for user_id, profile in self.user_profiles.items():
            if item_id in profile.get('recent_items', []):
                users.append(user_id)
        return users
    
    def _update_trending_window(self, interaction: UserInteraction):
        """Update sliding window for trending items"""
        current_time = datetime.fromisoformat(interaction.timestamp)
        
        # Add to window
        self.trending_window.append({
            'item_id': interaction.item_id,
            'timestamp': current_time,
            'weight': self._calculate_trend_weight(interaction)
        })
        
        # Remove old entries (keep 1 hour window)
        cutoff_time = current_time - timedelta(hours=1)
        self.trending_window = [
            entry for entry in self.trending_window
            if entry['timestamp'] > cutoff_time
        ]
        
        # Calculate and emit trending items every 100 interactions
        if len(self.trending_window) % 100 == 0:
            self._emit_trending_items()
    
    def _calculate_trend_weight(self, interaction: UserInteraction) -> float:
        """Calculate weight for trending calculation"""
        weight = 1.0
        
        # Higher weight for certain interactions
        if interaction.interaction_type == 'purchase':
            weight = 5.0
        elif interaction.interaction_type == 'add_to_cart':
            weight = 3.0
        elif interaction.interaction_type == 'like':
            weight = 2.0
        
        # Consider rating if available
        if interaction.rating:
            weight *= (interaction.rating / 5.0)
        
        return weight
    
    def _emit_trending_items(self):
        """Calculate and emit current trending items"""
        trend_scores = Counter()
        
        for entry in self.trending_window:
            # Recent items get higher weight
            time_decay = 1.0  # Could implement exponential decay
            trend_scores[entry['item_id']] += entry['weight'] * time_decay
        
        trending = [
            {'item_id': item, 'score': score}
            for item, score in trend_scores.most_common(50)
        ]
        
        # Emit to Kafka
        self.producer.produce(
            'trending-items',
            json.dumps({
                'trending_items': trending,
                'timestamp': datetime.utcnow().isoformat(),
                'window_size': len(self.trending_window)
            })
        )
        
        # Cache in Redis
        self.redis_client.setex(
            'trending_items',
            300,
            json.dumps(trending)
        )
        
        logger.info(f"Emitted {len(trending)} trending items")
    
    def run(self):
        """Main processing loop"""
        self.consumer.subscribe(['user-interactions'])
        logger.info("Stream processor started")
        
        try:
            while True:
                msg = self.consumer.poll(1.0)
                
                if msg is None:
                    continue
                    
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        continue
                
                try:
                    # Parse interaction
                    data = json.loads(msg.value().decode('utf-8'))
                    interaction = UserInteraction(**data)
                    
                    # Process interaction
                    self.process_interaction(interaction)
                    
                    # Flush producer periodically
                    self.producer.poll(0)
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except KeyboardInterrupt:
            logger.info("Shutting down stream processor")
        finally:
            self.consumer.close()
            self.producer.flush()


if __name__ == "__main__":
    processor = StreamProcessor()
    processor.run()