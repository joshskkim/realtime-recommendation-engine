"""
Cold Start Problem Handler
Provides strategies for handling new users and new items
"""

import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import numpy as np
from collections import Counter
import redis
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UserDemographics:
    """User demographic information"""
    age_group: Optional[str]
    gender: Optional[str]
    location: Optional[str]
    interests: List[str]
    registration_date: str


class ColdStartHandler:
    """Handles cold start problems for new users and items"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.strategies = {
            'popularity': self.popularity_based,
            'demographic': self.demographic_based,
            'category': self.category_based,
            'hybrid': self.hybrid_approach,
            'explore': self.exploration_based
        }
        
    def get_recommendations_for_new_user(
        self,
        user_id: str,
        demographics: Optional[UserDemographics] = None,
        limit: int = 10,
        strategy: str = 'hybrid'
    ) -> List[Dict[str, Any]]:
        """Get recommendations for a new user with no interaction history"""
        
        logger.info(f"Handling cold start for new user: {user_id}")
        
        if strategy not in self.strategies:
            strategy = 'hybrid'
            
        recommendations = self.strategies[strategy](
            user_id=user_id,
            demographics=demographics,
            limit=limit
        )
        
        # Add exploration items
        exploration_items = self._get_exploration_items(limit=3)
        
        # Combine and deduplicate
        combined = self._combine_recommendations(
            recommendations, 
            exploration_items,
            limit
        )
        
        # Cache the recommendations
        self._cache_recommendations(user_id, combined, strategy)
        
        return combined
    
    def get_recommendations_for_new_item(
        self,
        item_id: str,
        item_features: Dict[str, Any],
        limit: int = 10
    ) -> List[str]:
        """Get users to recommend a new item to"""
        
        logger.info(f"Handling cold start for new item: {item_id}")
        
        # Find similar items based on features
        similar_items = self._find_similar_items(item_features)
        
        # Get users who liked similar items
        target_users = []
        for similar_item in similar_items[:5]:
            users = self._get_users_who_liked_item(similar_item['item_id'])
            target_users.extend(users)
        
        # Deduplicate and rank users
        user_scores = Counter(target_users)
        ranked_users = [user for user, _ in user_scores.most_common(limit)]
        
        # Add early adopters
        early_adopters = self._get_early_adopters(limit=3)
        
        # Combine results
        final_users = list(set(ranked_users + early_adopters))[:limit]
        
        logger.info(f"Recommending item {item_id} to {len(final_users)} users")
        
        return final_users
    
    def popularity_based(
        self,
        user_id: str,
        demographics: Optional[UserDemographics] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Return most popular items overall"""
        
        # Get global popular items
        popular_items = self._get_popular_items(time_window_hours=168)  # Last week
        
        recommendations = []
        for item in popular_items[:limit]:
            recommendations.append({
                'item_id': item['item_id'],
                'score': item['popularity_score'],
                'reason': 'trending_globally',
                'strategy': 'popularity'
            })
        
        return recommendations
    
    def demographic_based(
        self,
        user_id: str,
        demographics: Optional[UserDemographics] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Return items popular among similar demographic groups"""
        
        if not demographics:
            return self.popularity_based(user_id, demographics, limit)
        
        # Get items popular in demographic group
        demographic_key = self._get_demographic_key(demographics)
        demographic_items = self._get_demographic_popular_items(demographic_key)
        
        recommendations = []
        for item in demographic_items[:limit]:
            recommendations.append({
                'item_id': item['item_id'],
                'score': item['score'],
                'reason': f'popular_in_{demographic_key}',
                'strategy': 'demographic'
            })
        
        return recommendations
    
    def category_based(
        self,
        user_id: str,
        demographics: Optional[UserDemographics] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Return diverse items from different categories"""
        
        categories = self._get_categories()
        items_per_category = max(1, limit // len(categories))
        
        recommendations = []
        for category in categories:
            category_items = self._get_top_items_in_category(
                category, 
                limit=items_per_category
            )
            
            for item in category_items:
                recommendations.append({
                    'item_id': item['item_id'],
                    'score': item['score'],
                    'reason': f'top_in_{category}',
                    'strategy': 'category'
                })
        
        return recommendations[:limit]
    
    def hybrid_approach(
        self,
        user_id: str,
        demographics: Optional[UserDemographics] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Combine multiple strategies for cold start"""
        
        # Weight distribution
        weights = {
            'popularity': 0.4,
            'demographic': 0.3,
            'category': 0.2,
            'explore': 0.1
        }
        
        all_recommendations = []
        
        # Get recommendations from each strategy
        for strategy, weight in weights.items():
            if strategy == 'hybrid':
                continue
                
            strategy_limit = int(limit * weight) + 1
            
            if strategy == 'demographic' and not demographics:
                # Fall back to popularity if no demographics
                recs = self.popularity_based(user_id, None, strategy_limit)
            else:
                recs = self.strategies.get(strategy, self.popularity_based)(
                    user_id=user_id,
                    demographics=demographics,
                    limit=strategy_limit
                )
            
            all_recommendations.extend(recs)
        
        # Deduplicate and score
        seen_items = set()
        final_recommendations = []
        
        for rec in all_recommendations:
            if rec['item_id'] not in seen_items:
                seen_items.add(rec['item_id'])
                # Adjust score based on multiple strategies
                rec['score'] = rec.get('score', 0.5) * weights.get(rec['strategy'], 0.1)
                rec['reason'] = 'hybrid_cold_start'
                final_recommendations.append(rec)
        
        # Sort by score and return top N
        final_recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return final_recommendations[:limit]
    
    def exploration_based(
        self,
        user_id: str,
        demographics: Optional[UserDemographics] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Return diverse items for exploration"""
        
        # Get random diverse items
        exploration_items = self._get_exploration_items(limit)
        
        recommendations = []
        for item in exploration_items:
            recommendations.append({
                'item_id': item['item_id'],
                'score': 0.5,  # Neutral score for exploration
                'reason': 'exploration',
                'strategy': 'explore'
            })
        
        return recommendations
    
    def _get_popular_items(self, time_window_hours: int = 24) -> List[Dict]:
        """Get globally popular items"""
        key = f"popular_items:{time_window_hours}h"
        cached = self.redis.get(key)
        
        if cached:
            return json.loads(cached)
        
        # In production, would query from database
        # For now, return mock data
        items = [
            {'item_id': f'popular_{i}', 'popularity_score': 1.0 - (i * 0.05)}
            for i in range(20)
        ]
        
        self.redis.setex(key, 3600, json.dumps(items))
        return items
    
    def _get_demographic_popular_items(self, demographic_key: str) -> List[Dict]:
        """Get items popular in a demographic group"""
        key = f"demographic_popular:{demographic_key}"
        cached = self.redis.get(key)
        
        if cached:
            return json.loads(cached)
        
        # Mock data - in production would query database
        items = [
            {'item_id': f'demo_{demographic_key}_{i}', 'score': 0.9 - (i * 0.05)}
            for i in range(15)
        ]
        
        self.redis.setex(key, 3600, json.dumps(items))
        return items
    
    def _get_categories(self) -> List[str]:
        """Get available categories"""
        categories = self.redis.get('categories')
        if categories:
            return json.loads(categories)
        
        # Default categories
        return ['electronics', 'books', 'clothing', 'sports', 'home']
    
    def _get_top_items_in_category(self, category: str, limit: int = 5) -> List[Dict]:
        """Get top items in a category"""
        key = f"category_top:{category}"
        cached = self.redis.get(key)
        
        if cached:
            items = json.loads(cached)
            return items[:limit]
        
        # Mock data
        items = [
            {'item_id': f'cat_{category}_{i}', 'score': 0.8 - (i * 0.05)}
            for i in range(10)
        ]
        
        self.redis.setex(key, 3600, json.dumps(items))
        return items[:limit]
    
    def _get_exploration_items(self, limit: int = 5) -> List[Dict]:
        """Get diverse items for exploration"""
        # In production, would use item embeddings for diversity
        # For now, return random selection
        items = []
        categories = self._get_categories()
        
        for i, cat in enumerate(categories[:limit]):
            items.append({
                'item_id': f'explore_{cat}_{i}',
                'category': cat
            })
        
        return items
    
    def _find_similar_items(self, item_features: Dict) -> List[Dict]:
        """Find items similar to given features"""
        # In production, would use content-based similarity
        # For now, return mock similar items
        return [
            {'item_id': f'similar_{i}', 'similarity': 0.9 - (i * 0.1)}
            for i in range(10)
        ]
    
    def _get_users_who_liked_item(self, item_id: str) -> List[str]:
        """Get users who positively interacted with an item"""
        key = f"item_users:{item_id}"
        cached = self.redis.get(key)
        
        if cached:
            return json.loads(cached)
        
        # Mock data
        users = [f'user_{i}' for i in range(20)]
        return users
    
    def _get_early_adopters(self, limit: int = 5) -> List[str]:
        """Get users who tend to try new items"""
        key = "early_adopters"
        cached = self.redis.get(key)
        
        if cached:
            adopters = json.loads(cached)
            return adopters[:limit]
        
        # Mock data
        return [f'early_adopter_{i}' for i in range(limit)]
    
    def _get_demographic_key(self, demographics: UserDemographics) -> str:
        """Generate demographic key for grouping"""
        parts = []
        
        if demographics.age_group:
            parts.append(demographics.age_group)
        if demographics.gender:
            parts.append(demographics.gender)
        if demographics.location:
            parts.append(demographics.location.split(',')[0])  # Country only
        
        return '_'.join(parts) if parts else 'unknown'
    
    def _combine_recommendations(
        self,
        primary: List[Dict],
        secondary: List[Dict],
        limit: int
    ) -> List[Dict]:
        """Combine and deduplicate recommendation lists"""
        seen = set()
        combined = []
        
        for rec in primary + secondary:
            if rec['item_id'] not in seen:
                seen.add(rec['item_id'])
                combined.append(rec)
                
                if len(combined) >= limit:
                    break
        
        return combined
    
    def _cache_recommendations(
        self,
        user_id: str,
        recommendations: List[Dict],
        strategy: str
    ):
        """Cache cold start recommendations"""
        key = f"cold_start_recs:{user_id}"
        data = {
            'recommendations': recommendations,
            'strategy': strategy,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.redis.setex(key, 1800, json.dumps(data))  # 30 minutes