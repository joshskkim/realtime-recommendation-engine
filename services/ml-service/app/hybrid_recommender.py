# services/ml-service/app/hybrid_recommender.py
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime, timedelta
import logging
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import redis
import json

logger = logging.getLogger(__name__)

class HybridRecommender:
    """
    Hybrid recommendation engine combining multiple strategies:
    - Collaborative Filtering
    - Content-Based Filtering  
    - Popularity-Based
    - Context-Aware recommendations
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.strategies = {
            'collaborative': self._collaborative_filtering,
            'content': self._content_based,
            'popularity': self._popularity_based,
            'hybrid': self._hybrid_approach
        }
        
    async def generate_recommendations(
        self,
        user_id: str,
        user_profile: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        strategy: str = 'hybrid',
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate personalized recommendations using specified strategy
        """
        logger.info(f"Generating {strategy} recommendations for user {user_id}")
        
        # Get user interaction history
        interactions = await self._get_user_interactions(user_id)
        
        # Get candidate items
        candidates = await self._get_candidate_items(user_id, interactions)
        
        # Apply specified strategy
        if strategy not in self.strategies:
            strategy = 'hybrid'
            
        recommendations = await self.strategies[strategy](
            user_id, 
            user_profile,
            interactions,
            candidates,
            context
        )
        
        # Sort and limit results
        recommendations = sorted(
            recommendations,
            key=lambda x: x['score'],
            reverse=True
        )[:limit]
        
        # Add explanation for each recommendation
        recommendations = self._add_explanations(recommendations, strategy)
        
        return {
            'user_id': user_id,
            'strategy': strategy,
            'items': recommendations,
            'generated_at': datetime.utcnow().isoformat(),
            'context': context
        }
    
    async def _collaborative_filtering(
        self,
        user_id: str,
        user_profile: Optional[Dict],
        interactions: List[Dict],
        candidates: List[str],
        context: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """
        User-based collaborative filtering
        """
        # Get similar users
        similar_users = await self._find_similar_users(user_id, interactions)
        
        recommendations = []
        item_scores = defaultdict(float)
        
        # Aggregate scores from similar users
        for similar_user, similarity in similar_users[:20]:
            similar_interactions = await self._get_user_interactions(similar_user)
            
            for interaction in similar_interactions:
                if interaction['item_id'] not in [i['item_id'] for i in interactions]:
                    weight = similarity
                    if interaction.get('rating'):
                        weight *= (interaction['rating'] / 5.0)
                    item_scores[interaction['item_id']] += weight
        
        # Normalize and create recommendation objects
        max_score = max(item_scores.values()) if item_scores else 1.0
        for item_id, score in item_scores.items():
            if item_id in candidates:
                recommendations.append({
                    'item_id': item_id,
                    'score': score / max_score,
                    'method': 'collaborative'
                })
        
        return recommendations
    
    async def _content_based(
        self,
        user_id: str,
        user_profile: Optional[Dict],
        interactions: List[Dict],
        candidates: List[str],
        context: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Content-based filtering using item features
        """
        recommendations = []
        
        # Build user preference vector from interactions
        user_vector = await self._build_user_preference_vector(user_id, interactions)
        
        # Calculate similarity with candidate items
        for item_id in candidates:
            item_vector = await self._get_item_features(item_id)
            if item_vector is not None:
                similarity = self._calculate_similarity(user_vector, item_vector)
                
                # Boost score based on user profile preferences
                if user_profile and user_profile.get('preferences'):
                    for pref in user_profile['preferences']:
                        if await self._item_matches_preference(item_id, pref):
                            similarity *= (1 + pref.get('weight', 0.1))
                
                recommendations.append({
                    'item_id': item_id,
                    'score': similarity,
                    'method': 'content'
                })
        
        return recommendations
    
    async def _popularity_based(
        self,
        user_id: str,
        user_profile: Optional[Dict],
        interactions: List[Dict],
        candidates: List[str],
        context: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Popularity-based recommendations with time decay
        """
        recommendations = []
        
        # Get trending items with time windows
        time_windows = {
            '1h': timedelta(hours=1),
            '24h': timedelta(days=1),
            '7d': timedelta(days=7)
        }
        
        popularity_scores = defaultdict(float)
        
        for window_name, window_delta in time_windows.items():
            trending = await self._get_trending_items(window_delta)
            
            # Apply time decay
            decay_factor = 1.0 / (1 + len(time_windows) - list(time_windows.keys()).index(window_name))
            
            for item_id, count in trending.items():
                if item_id in candidates:
                    popularity_scores[item_id] += count * decay_factor
        
        # Normalize scores
        max_score = max(popularity_scores.values()) if popularity_scores else 1.0
        
        for item_id, score in popularity_scores.items():
            recommendations.append({
                'item_id': item_id,
                'score': score / max_score,
                'method': 'popularity'
            })
        
        return recommendations
    
    async def _hybrid_approach(
        self,
        user_id: str,
        user_profile: Optional[Dict],
        interactions: List[Dict],
        candidates: List[str],
        context: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Combine multiple recommendation strategies with adaptive weights
        """
        # Determine weights based on user characteristics
        weights = self._calculate_strategy_weights(user_id, user_profile, interactions)
        
        # Get recommendations from each strategy
        all_recommendations = {}
        
        for strategy_name, strategy_func in [
            ('collaborative', self._collaborative_filtering),
            ('content', self._content_based),
            ('popularity', self._popularity_based)
        ]:
            if weights.get(strategy_name, 0) > 0:
                strategy_recs = await strategy_func(
                    user_id, user_profile, interactions, candidates, context
                )
                
                # Aggregate scores
                for rec in strategy_recs:
                    item_id = rec['item_id']
                    if item_id not in all_recommendations:
                        all_recommendations[item_id] = {
                            'item_id': item_id,
                            'score': 0,
                            'methods': []
                        }
                    
                    all_recommendations[item_id]['score'] += (
                        rec['score'] * weights[strategy_name]
                    )
                    all_recommendations[item_id]['methods'].append(strategy_name)
        
        # Convert to list and add method info
        recommendations = []
        for item_id, data in all_recommendations.items():
            recommendations.append({
                'item_id': item_id,
                'score': data['score'],
                'method': 'hybrid',
                'contributing_methods': data['methods']
            })
        
        return recommendations
    
    def _calculate_strategy_weights(
        self,
        user_id: str,
        user_profile: Optional[Dict],
        interactions: List[Dict]
    ) -> Dict[str, float]:
        """
        Calculate adaptive weights for each strategy based on user characteristics
        """
        weights = {
            'collaborative': 0.4,
            'content': 0.4,
            'popularity': 0.2
        }
        
        # New users get more popularity-based recommendations
        if len(interactions) < 5:
            weights['popularity'] = 0.6
            weights['collaborative'] = 0.1
            weights['content'] = 0.3
        
        # Users with rich profiles get more content-based
        elif user_profile and user_profile.get('preferences'):
            weights['content'] = 0.5
            weights['collaborative'] = 0.35
            weights['popularity'] = 0.15
        
        # Active users get more collaborative filtering
        elif len(interactions) > 50:
            weights['collaborative'] = 0.6
            weights['content'] = 0.3
            weights['popularity'] = 0.1
        
        return weights
    
    def _add_explanations(
        self,
        recommendations: List[Dict],
        strategy: str
    ) -> List[Dict]:
        """
        Add human-readable explanations for recommendations
        """
        explanations = {
            'collaborative': 'Users with similar tastes also liked this',
            'content': 'Based on your preferences and past interactions',
            'popularity': 'Trending and popular right now',
            'hybrid': 'Personalized recommendation combining multiple factors'
        }
        
        for rec in recommendations:
            method = rec.get('method', strategy)
            rec['explanation'] = explanations.get(method, 'Recommended for you')
            
            # Add more specific explanation for hybrid
            if method == 'hybrid' and 'contributing_methods' in rec:
                methods = rec['contributing_methods']
                if 'collaborative' in methods and 'content' in methods:
                    rec['explanation'] = 'Matches your preferences and liked by similar users'
                elif 'popularity' in methods:
                    rec['explanation'] = 'Popular and tailored to your interests'
        
        return recommendations
    
    async def _get_user_interactions(self, user_id: str) -> List[Dict]:
        """Get user interaction history from Redis"""
        key = f"user:interactions:{user_id}"
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return []
    
    async def _get_candidate_items(
        self,
        user_id: str,
        interactions: List[Dict]
    ) -> List[str]:
        """Get candidate items for recommendation"""
        # Get all available items
        all_items = self.redis.smembers("items:all")
        
        # Filter out already interacted items
        interacted = {i['item_id'] for i in interactions}
        candidates = [item.decode() for item in all_items if item.decode() not in interacted]
        
        return candidates
    
    async def _find_similar_users(
        self,
        user_id: str,
        interactions: List[Dict]
    ) -> List[tuple]:
        """Find users with similar interaction patterns"""
        similar_users = []
        
        # Get all users
        all_users = self.redis.smembers("users:all")
        
        for other_user in all_users:
            other_id = other_user.decode()
            if other_id != user_id:
                other_interactions = await self._get_user_interactions(other_id)
                similarity = self._calculate_user_similarity(interactions, other_interactions)
                if similarity > 0.1:  # Threshold
                    similar_users.append((other_id, similarity))
        
        return sorted(similar_users, key=lambda x: x[1], reverse=True)
    
    def _calculate_user_similarity(
        self,
        interactions1: List[Dict],
        interactions2: List[Dict]
    ) -> float:
        """Calculate similarity between two users based on interactions"""
        # Create item sets
        items1 = {i['item_id'] for i in interactions1}
        items2 = {i['item_id'] for i in interactions2}
        
        if not items1 or not items2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(items1 & items2)
        union = len(items1 | items2)
        
        return intersection / union if union > 0 else 0.0
    
    async def _build_user_preference_vector(
        self,
        user_id: str,
        interactions: List[Dict]
    ) -> np.ndarray:
        """Build user preference vector from interactions"""
        # Simple TF-IDF style vector (can be enhanced)
        vector = np.zeros(100)  # Assuming 100-dimensional feature space
        
        for interaction in interactions:
            item_features = await self._get_item_features(interaction['item_id'])
            if item_features is not None:
                # Weight by rating if available
                weight = interaction.get('rating', 3.0) / 5.0
                vector += item_features * weight
        
        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector /= norm
            
        return vector
    
    async def _get_item_features(self, item_id: str) -> Optional[np.ndarray]:
        """Get feature vector for an item"""
        key = f"item:features:{item_id}"
        data = self.redis.get(key)
        if data:
            return np.array(json.loads(data))
        
        # Generate random features for demo (should be real features)
        features = np.random.rand(100)
        self.redis.setex(key, 3600, json.dumps(features.tolist()))
        return features
    
    def _calculate_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        similarity = cosine_similarity([vector1], [vector2])[0][0]
        return max(0.0, similarity)  # Ensure non-negative
    
    async def _item_matches_preference(self, item_id: str, preference: Dict) -> bool:
        """Check if item matches user preference"""
        # Get item metadata
        key = f"item:metadata:{item_id}"
        metadata = self.redis.get(key)
        
        if metadata:
            item_data = json.loads(metadata)
            category = item_data.get('category', '')
            tags = item_data.get('tags', [])
            
            # Check category match
            if preference.get('category') == category:
                return True
            
            # Check tag overlap
            pref_tags = preference.get('tags', [])
            if set(tags) & set(pref_tags):
                return True
        
        return False
    
    async def _get_trending_items(self, time_window: timedelta) -> Dict[str, int]:
        """Get trending items within a time window"""
        # Get interaction counts from Redis sorted set
        key = f"trending:items:{int(time_window.total_seconds())}"
        items = self.redis.zrevrange(key, 0, 100, withscores=True)
        
        return {item.decode(): int(score) for item, score in items}