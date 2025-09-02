"""
Integration of A/B Testing with recommendation algorithms
File: services/ml-service/app/core/recommendation_strategies.py
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import numpy as np
import redis
from app.core.ab_testing import ABTestingFramework


@dataclass
class RecommendationStrategy:
    """Base recommendation strategy"""
    name: str
    algorithm: str
    parameters: Dict[str, Any]


class StrategyManager:
    """Manages different recommendation strategies for A/B testing"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ab_framework = ABTestingFramework(redis_client)
        
        # Define available strategies
        self.strategies = {
            'standard': self.standard_collaborative_filtering,
            'enhanced_cf': self.enhanced_collaborative_filtering,
            'hybrid_v1': self.hybrid_algorithm_v1,
            'hybrid_v2': self.hybrid_algorithm_v2,
            'deep_learning': self.deep_learning_based,
            'context_aware': self.context_aware_recommendations,
            'real_time': self.real_time_personalization
        }
    
    def get_recommendations(
        self,
        user_id: str,
        experiment_id: Optional[str] = None,
        limit: int = 10,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Get recommendations with A/B test variant selection"""
        
        # Determine strategy based on A/B test
        if experiment_id:
            variant = self.ab_framework.get_user_variant(user_id, experiment_id)
            strategy = self._get_strategy_for_variant(experiment_id, variant)
        else:
            # Check for any active experiments
            active_experiment = self._get_active_experiment_for_user(user_id)
            if active_experiment:
                variant = self.ab_framework.get_user_variant(
                    user_id, 
                    active_experiment['id']
                )
                strategy = self._get_strategy_for_variant(
                    active_experiment['id'], 
                    variant
                )
                experiment_id = active_experiment['id']
            else:
                strategy = 'standard'
                variant = 'control'
        
        # Execute strategy
        recommendations = self.strategies[strategy](
            user_id=user_id,
            limit=limit,
            context=context
        )
        
        # Track recommendation generation
        if experiment_id:
            self.ab_framework.track_event(
                user_id=user_id,
                experiment_id=experiment_id,
                event_type='recommendations_generated',
                value=len(recommendations),
                metadata={'strategy': strategy}
            )
        
        return {
            'user_id': user_id,
            'recommendations': recommendations,
            'strategy': strategy,
            'variant': variant,
            'experiment_id': experiment_id
        }
    
    def standard_collaborative_filtering(
        self,
        user_id: str,
        limit: int,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """Standard collaborative filtering algorithm"""
        
        # Mock implementation - replace with actual CF
        items = []
        for i in range(limit):
            items.append({
                'item_id': f'cf_item_{i}',
                'score': 0.9 - (i * 0.05),
                'reason': 'collaborative_filtering'
            })
        
        return items
    
    def enhanced_collaborative_filtering(
        self,
        user_id: str,
        limit: int,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """Enhanced CF with temporal weighting"""
        
        # Enhanced version with time decay
        items = []
        for i in range(limit):
            items.append({
                'item_id': f'enhanced_cf_item_{i}',
                'score': 0.95 - (i * 0.04),
                'reason': 'enhanced_collaborative_filtering',
                'time_weight': 0.8
            })
        
        return items
    
    def hybrid_algorithm_v1(
        self,
        user_id: str,
        limit: int,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """Hybrid: 50% CF, 30% content, 20% popularity"""
        
        cf_items = self.standard_collaborative_filtering(
            user_id, 
            int(limit * 0.5), 
            context
        )
        
        # Add content-based items
        content_items = [
            {
                'item_id': f'content_item_{i}',
                'score': 0.85 - (i * 0.05),
                'reason': 'content_based'
            }
            for i in range(int(limit * 0.3))
        ]
        
        # Add popular items
        popular_items = [
            {
                'item_id': f'popular_item_{i}',
                'score': 0.8 - (i * 0.05),
                'reason': 'popularity'
            }
            for i in range(int(limit * 0.2))
        ]
        
        # Combine and sort
        all_items = cf_items + content_items + popular_items
        all_items.sort(key=lambda x: x['score'], reverse=True)
        
        return all_items[:limit]
    
    def hybrid_algorithm_v2(
        self,
        user_id: str,
        limit: int,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """Hybrid: Dynamic weights based on user profile"""
        
        # Get user profile to determine weights
        user_profile = self._get_user_profile(user_id)
        
        # Dynamic weight calculation
        if user_profile.get('interaction_count', 0) < 10:
            # New user: more popularity
            weights = {'cf': 0.2, 'content': 0.3, 'popularity': 0.5}
        else:
            # Active user: more personalization
            weights = {'cf': 0.6, 'content': 0.3, 'popularity': 0.1}
        
        items = []
        for strategy, weight in weights.items():
            strategy_limit = int(limit * weight)
            if strategy == 'cf':
                items.extend(self.standard_collaborative_filtering(
                    user_id, strategy_limit, context
                ))
        
        return items[:limit]
    
    def deep_learning_based(
        self,
        user_id: str,
        limit: int,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """Deep learning based recommendations"""
        
        # Mock deep learning predictions
        items = []
        for i in range(limit):
            items.append({
                'item_id': f'dl_item_{i}',
                'score': float(np.random.beta(8, 2)),  # Skewed distribution
                'reason': 'deep_learning',
                'model_confidence': 0.85
            })
        
        items.sort(key=lambda x: x['score'], reverse=True)
        return items
    
    def context_aware_recommendations(
        self,
        user_id: str,
        limit: int,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """Context-aware recommendations (time, location, device)"""
        
        # Use context for personalization
        time_of_day = context.get('time_of_day', 'evening') if context else 'evening'
        device = context.get('device', 'mobile') if context else 'mobile'
        
        items = []
        for i in range(limit):
            items.append({
                'item_id': f'context_{time_of_day}_{device}_{i}',
                'score': 0.88 - (i * 0.04),
                'reason': 'context_aware',
                'context': {'time': time_of_day, 'device': device}
            })
        
        return items
    
    def real_time_personalization(
        self,
        user_id: str,
        limit: int,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """Real-time personalization based on session data"""
        
        # Get current session data
        session_key = f"session:{user_id}"
        session_data = self.redis.get(session_key)
        
        items = []
        if session_data:
            # Personalize based on session
            for i in range(limit):
                items.append({
                    'item_id': f'realtime_item_{i}',
                    'score': 0.92 - (i * 0.03),
                    'reason': 'real_time_session'
                })
        else:
            # Fallback to standard
            items = self.standard_collaborative_filtering(user_id, limit, context)
        
        return items
    
    def _get_strategy_for_variant(
        self,
        experiment_id: str,
        variant: str
    ) -> str:
        """Get strategy name for experiment variant"""
        
        experiment = self.ab_framework.experiments.get(experiment_id)
        if not experiment:
            return 'standard'
        
        if variant == 'control':
            return experiment.control_group.get('algorithm', 'standard')
        
        # Find treatment group
        for treatment in experiment.treatment_groups:
            if treatment['name'] == variant:
                return treatment.get('algorithm', 'standard')
        
        return 'standard'
    
    def _get_active_experiment_for_user(
        self,
        user_id: str
    ) -> Optional[Dict]:
        """Check if user should be in any active experiment"""
        
        from app.core.ab_testing import ExperimentStatus
        
        for exp_id, config in self.ab_framework.experiments.items():
            if config.status == ExperimentStatus.RUNNING:
                # Check if user meets criteria
                # Could add targeting rules here
                return {'id': exp_id, 'name': config.name}
        
        return None
    
    def _get_user_profile(self, user_id: str) -> Dict:
        """Get user profile from cache"""
        
        profile_key = f"user_profile:{user_id}"
        profile = self.redis.get(profile_key)
        
        if profile:
            import json
            return json.loads(profile)
        
        return {}