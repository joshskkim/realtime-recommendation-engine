"""
Main recommendation service orchestrating different algorithms
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta

from ..models.database import get_db, Interaction, User, Item, UserProfile, ItemFeatures
from ..models.collaborative_filtering import CollaborativeFilter, UserBasedCF
from .cache_service import CacheService
from .kafka_service import KafkaService

logger = logging.getLogger(__name__)


class RecommendationService:
    """Main service for generating recommendations"""
    
    def __init__(self, cache_service: CacheService, kafka_service: KafkaService):
        self.cache_service = cache_service
        self.kafka_service = kafka_service
        self.cf_model = CollaborativeFilter(n_factors=50, min_interactions=5)
        self.user_cf_model = UserBasedCF()
        self.is_model_trained = False
        self.last_training = None
        
        # Configuration
        self.hybrid_weights = {
            "collaborative": 0.4,
            "content_based": 0.4,
            "popularity": 0.2
        }
    
    async def start(self):
        """Initialize the recommendation service"""
        logger.info("🤖 Starting recommendation service...")
        await self.train_models()
        logger.info("✅ Recommendation service ready")
    
    async def train_models(self):
        """Train recommendation models"""
        try:
            logger.info("📚 Training recommendation models...")
            
            # Get training data
            db = next(get_db())
            
            # Load interactions
            interactions = db.query(Interaction).filter(
                Interaction.timestamp >= datetime.now() - timedelta(days=90)
            ).all()
            
            if not interactions:
                logger.warning("No interactions found for training")
                return
            
            # Convert to DataFrame
            interaction_data = []
            for interaction in interactions:
                interaction_data.append({
                    'user_id': interaction.user_id,
                    'item_id': interaction.item_id,
                    'rating': interaction.rating or self._implicit_rating(interaction.interaction_type),
                    'timestamp': interaction.timestamp
                })
            
            df = pd.DataFrame(interaction_data)
            
            # Train collaborative filtering
            self.cf_model.fit(df)
            self.user_cf_model.fit(df)
            
            self.is_model_trained = True
            self.last_training = datetime.now()
            
            logger.info(f"✅ Models trained with {len(df)} interactions")
            
        except Exception as e:
            logger.error(f"❌ Error training models: {e}")
        finally:
            db.close()
    
    def _implicit_rating(self, interaction_type: str) -> float:
        """Convert implicit feedback to rating"""
        mapping = {
            'view': 1.0,
            'like': 4.0,
            'dislike': 2.0,
            'share': 4.5,
            'purchase': 5.0,
            'rating': 3.0  # fallback
        }
        return mapping.get(interaction_type, 3.0)
    
    async def get_recommendations(self, user_id: int, limit: int = 10,
                                algorithm: str = "hybrid") -> List[Dict[str, Any]]:
        """Get recommendations for a user"""
        
        # Check cache first
        cached_recs = await self.cache_service.get_recommendations(user_id, algorithm)
        if cached_recs:
            logger.debug(f"Returning cached recommendations for user {user_id}")
            return cached_recs[:limit]
        
        # Generate new recommendations
        recommendations = []
        
        try:
            if algorithm == "hybrid":
                recommendations = await self._get_hybrid_recommendations(user_id, limit)
            elif algorithm == "collaborative":
                recommendations = await self._get_collaborative_recommendations(user_id, limit)
            elif algorithm == "content":
                recommendations = await self._get_content_based_recommendations(user_id, limit)
            elif algorithm == "popularity":
                recommendations = await self._get_popularity_recommendations(user_id, limit)
            else:
                # Default to hybrid
                recommendations = await self._get_hybrid_recommendations(user_id, limit)
            
            # Cache the recommendations
            if recommendations:
                await self.cache_service.cache_recommendations(user_id, recommendations, algorithm)
            
            # Publish recommendation event to Kafka
            await self.kafka_service.publish_recommendation_event({
                "user_id": user_id,
                "algorithm": algorithm,
                "recommendation_count": len(recommendations),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error generating recommendations for user {user_id}: {e}")
            # Fallback to popular items
            recommendations = await self._get_popularity_recommendations(user_id, limit)
        
        return recommendations[:limit]
    
    async def _get_hybrid_recommendations(self, user_id: int, limit: int) -> List[Dict[str, Any]]:
        """Generate hybrid recommendations combining multiple algorithms"""
        
        # Get recommendations from each algorithm
        cf_recs = await self._get_collaborative_recommendations(user_id, limit * 2)
        content_recs = await self._get_content_based_recommendations(user_id, limit * 2)
        popularity_recs = await self._get_popularity_recommendations(user_id, limit * 2)
        
        # Combine and weight scores
        item_scores = {}
        
        # Add collaborative filtering scores
        for rec in cf_recs:
            item_id = rec['item_id']
            weighted_score = rec['score'] * self.hybrid_weights['collaborative']
            item_scores[item_id] = item_scores.get(item_id, 0) + weighted_score
        
        # Add content-based scores
        for rec in content_recs:
            item_id = rec['item_id']
            weighted_score = rec['score'] * self.hybrid_weights['content_based']
            item_scores[item_id] = item_scores.get(item_id, 0) + weighted_score
        
        # Add popularity scores
        for rec in popularity_recs:
            item_id = rec['item_id']
            weighted_score = rec['score'] * self.hybrid_weights['popularity']
            item_scores[item_id] = item_scores.get(item_id, 0) + weighted_score
        
        # Sort by combined score
        sorted_items = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get item details and format recommendations
        db = next(get_db())
        recommendations = []
        
        try:
            for item_id, score in sorted_items[:limit]:
                item = db.query(Item).filter(Item.item_id == item_id).first()
                if item:
                    recommendations.append({
                        'item_id': item_id,
                        'title': item.title,
                        'category': item.category,
                        'score': round(score, 3),
                        'algorithm': 'hybrid',
                        'explanation': self._generate_explanation(item, score)
                    })
        finally:
            db.close()
        
        return recommendations
    
    async def _get_collaborative_recommendations(self, user_id: int, limit: int) -> List[Dict[str, Any]]:
        """Get collaborative filtering recommendations"""
        if not self.is_model_trained:
            return []
        
        try:
            # Get CF recommendations
            cf_recs = self.cf_model.get_user_recommendations(user_id, limit)
            
            if not cf_recs:
                return []
            
            # Format recommendations with item details
            db = next(get_db())
            recommendations = []
            
            try:
                for item_id, score in cf_recs:
                    item = db.query(Item).filter(Item.item_id == item_id).first()
                    if item:
                        recommendations.append({
                            'item_id': item_id,
                            'title': item.title,
                            'category': item.category,
                            'score': round(score, 3),
                            'algorithm': 'collaborative',
                            'explanation': f'Users with similar preferences liked this'
                        })
            finally:
                db.close()
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in collaborative filtering: {e}")
            return []
    
    async def _get_content_based_recommendations(self, user_id: int, limit: int) -> List[Dict[str, Any]]:
        """Get content-based recommendations"""
        db = next(get_db())
        recommendations = []
        
        try:
            # Get user's interaction history
            user_interactions = db.query(Interaction).filter(
                Interaction.user_id == user_id
            ).join(Item).all()
            
            if not user_interactions:
                return []
            
            # Get user's preferred categories
            user_categories = {}
            for interaction in user_interactions:
                category = interaction.item.category
                if category:
                    rating = interaction.rating or self._implicit_rating(interaction.interaction_type)
                    user_categories[category] = user_categories.get(category, [])
                    user_categories[category].append(rating)
            
            # Calculate average rating per category
            category_preferences = {}
            for category, ratings in user_categories.items():
                category_preferences[category] = np.mean(ratings)
            
            # Find items in preferred categories that user hasn't seen
            seen_items = {interaction.item_id for interaction in user_interactions}
            
            recommended_items = db.query(Item).filter(
                Item.category.in_(category_preferences.keys()),
                ~Item.item_id.in_(seen_items)
            ).limit(limit * 2).all()
            
            # Score items based on category preference
            for item in recommended_items:
                if item.category in category_preferences:
                    score = category_preferences[item.category] / 5.0  # Normalize to 0-1
                    recommendations.append({
                        'item_id': item.item_id,
                        'title': item.title,
                        'category': item.category,
                        'score': round(score, 3),
                        'algorithm': 'content_based',
                        'explanation': f'Similar to items you liked in {item.category}'
                    })
            
            # Sort by score
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error in content-based recommendations: {e}")
        finally:
            db.close()
        
        return recommendations[:limit]
    
    async def _get_popularity_recommendations(self, user_id: int, limit: int) -> List[Dict[str, Any]]:
        """Get popularity-based recommendations"""
        
        # Check cache first
        cached_popular = await self.cache_service.get_popular_items("all", limit)
        if cached_popular:
            return cached_popular
        
        db = next(get_db())
        recommendations = []
        
        try:
            # Get user's seen items to exclude
            seen_items = set()
            user_interactions = db.query(Interaction.item_id).filter(
                Interaction.user_id == user_id
            ).all()
            seen_items = {item_id for (item_id,) in user_interactions}
            
            # Get popular items based on interaction count and ratings
            popular_items_query = """
                SELECT 
                    i.item_id,
                    i.title,
                    i.category,
                    COUNT(int.interaction_id) as interaction_count,
                    AVG(CASE WHEN int.rating IS NOT NULL THEN int.rating ELSE 3.0 END) as avg_rating,
                    COUNT(int.interaction_id) * 0.7 + AVG(CASE WHEN int.rating IS NOT NULL THEN int.rating ELSE 3.0 END) * 0.3 as popularity_score
                FROM items i
                LEFT JOIN interactions int ON i.item_id = int.item_id
                WHERE i.item_id NOT IN :seen_items OR :has_seen_items = false
                GROUP BY i.item_id, i.title, i.category
                HAVING COUNT(int.interaction_id) > 0
                ORDER BY popularity_score DESC
                LIMIT :limit
            """
            
            result = db.execute(
                popular_items_query,
                {
                    "seen_items": tuple(seen_items) if seen_items else (0,),
                    "has_seen_items": len(seen_items) > 0,
                    "limit": limit
                }
            ).fetchall()
            
            max_score = max([row.popularity_score for row in result]) if result else 1.0
            
            for row in result:
                normalized_score = row.popularity_score / max_score
                recommendations.append({
                    'item_id': row.item_id,
                    'title': row.title,
                    'category': row.category,
                    'score': round(normalized_score, 3),
                    'algorithm': 'popularity',
                    'explanation': f'Popular item with {row.interaction_count} interactions'
                })
            
            # Cache popular items
            if recommendations:
                await self.cache_service.cache_popular_items(recommendations, "all")
            
        except Exception as e:
            logger.error(f"Error getting popular items: {e}")
        finally:
            db.close()
        
        return recommendations
    
    def _generate_explanation(self, item: Item, score: float) -> str:
        """Generate explanation for recommendation"""
        if score > 0.8:
            return f"Highly recommended based on your preferences"
        elif score > 0.6:
            return f"Good match for your interests in {item.category}"
        else:
            return f"You might like this {item.category} content"
    
    async def get_similar_items(self, item_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get items similar to the given item"""
        
        # Check cache first
        cached_similar = await self.cache_service.get_similar_items(item_id)
        if cached_similar:
            return cached_similar[:limit]
        
        if not self.is_model_trained:
            return []
        
        try:
            # Get similar items from collaborative filtering
            similar_items = self.cf_model.get_similar_items(item_id, limit)
            
            if not similar_items:
                return []
            
            # Format with item details
            db = next(get_db())
            recommendations = []
            
            try:
                for similar_item_id, similarity in similar_items:
                    item = db.query(Item).filter(Item.item_id == similar_item_id).first()
                    if item:
                        recommendations.append({
                            'item_id': similar_item_id,
                            'title': item.title,
                            'category': item.category,
                            'score': round(similarity, 3),
                            'algorithm': 'item_similarity',
                            'explanation': f'Similar to the item you\'re viewing'
                        })
                
                # Cache similar items
                if recommendations:
                    await self.cache_service.cache_similar_items(item_id, recommendations)
                
            finally:
                db.close()
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting similar items: {e}")
            return []
    
    async def record_interaction(self, user_id: int, item_id: int, 
                               interaction_type: str, rating: Optional[float] = None,
                               session_id: Optional[str] = None):
        """Record user interaction and invalidate cache"""
        
        db = next(get_db())
        
        try:
            # Create interaction record
            interaction = Interaction(
                user_id=user_id,
                item_id=item_id,
                interaction_type=interaction_type,
                rating=rating,
                session_id=session_id,
                timestamp=datetime.now()
            )
            
            db.add(interaction)
            db.commit()
            
            # Invalidate user's cache
            await self.cache_service.invalidate_user_cache(user_id)
            
            # Publish to Kafka
            await self.kafka_service.publish_interaction({
                "user_id": user_id,
                "item_id": item_id,
                "interaction_type": interaction_type,
                "rating": rating,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.debug(f"Recorded {interaction_type} interaction: user {user_id}, item {item_id}")
            
        except Exception as e:
            logger.error(f"Error recording interaction: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def get_model_stats(self) -> Dict[str, Any]:
        """Get recommendation model statistics"""
        return {
            "is_trained": self.is_model_trained,
            "last_training": self.last_training.isoformat() if self.last_training else None,
            "cf_users": len(self.cf_model.user_to_idx) if self.is_model_trained else 0,
            "cf_items": len(self.cf_model.item_to_idx) if self.is_model_trained else 0,
            "hybrid_weights": self.hybrid_weights
        }