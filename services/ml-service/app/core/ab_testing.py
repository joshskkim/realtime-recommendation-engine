"""
A/B Testing Framework for Recommendation Engine
Manages experiments, user assignment, and metrics tracking
"""

import json
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from scipy import stats
import redis

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class ExperimentConfig:
    """Configuration for an A/B test experiment"""
    experiment_id: str
    name: str
    description: str
    start_date: str
    end_date: Optional[str]
    status: ExperimentStatus
    control_group: Dict[str, Any]
    treatment_groups: List[Dict[str, Any]]
    metrics: List[str]
    target_sample_size: Optional[int]
    allocation: Dict[str, float]  # Group -> percentage
    metadata: Optional[Dict]


@dataclass
class ExperimentMetrics:
    """Metrics for experiment analysis"""
    group: str
    users: int
    conversions: int
    conversion_rate: float
    avg_engagement: float
    revenue: float
    confidence_interval: Tuple[float, float]
    p_value: Optional[float]
    is_significant: bool


class ABTestingFramework:
    """Manages A/B testing for recommendation strategies"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.experiments = {}
        self._load_experiments()
        
    def create_experiment(self, config: ExperimentConfig) -> str:
        """Create a new A/B test experiment"""
        logger.info(f"Creating experiment: {config.name}")
        
        # Validate configuration
        self._validate_experiment_config(config)
        
        # Store experiment
        self.experiments[config.experiment_id] = config
        self._save_experiment(config)
        
        # Initialize metrics tracking
        self._initialize_metrics(config.experiment_id)
        
        return config.experiment_id
    
    def get_user_variant(
        self,
        user_id: str,
        experiment_id: str
    ) -> Optional[str]:
        """Determine which variant a user should see"""
        
        # Check if experiment is running
        experiment = self.experiments.get(experiment_id)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return None
        
        # Check if user already assigned
        cached_variant = self._get_cached_assignment(user_id, experiment_id)
        if cached_variant:
            return cached_variant
        
        # Assign user to variant
        variant = self._assign_user_to_variant(user_id, experiment)
        
        # Cache assignment
        self._cache_assignment(user_id, experiment_id, variant)
        
        # Track assignment
        self._track_assignment(user_id, experiment_id, variant)
        
        return variant
    
    def track_event(
        self,
        user_id: str,
        experiment_id: str,
        event_type: str,
        value: Optional[float] = None,
        metadata: Optional[Dict] = None
    ):
        """Track user event for experiment"""
        
        variant = self.get_user_variant(user_id, experiment_id)
        if not variant:
            return
        
        # Store event
        event = {
            'user_id': user_id,
            'experiment_id': experiment_id,
            'variant': variant,
            'event_type': event_type,
            'value': value,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata
        }
        
        # Store in Redis
        key = f"exp_events:{experiment_id}:{variant}"
        self.redis.rpush(key, json.dumps(event))
        
        # Update metrics
        self._update_metrics(experiment_id, variant, event_type, value)
    
    def get_experiment_results(
        self,
        experiment_id: str
    ) -> Dict[str, ExperimentMetrics]:
        """Get current results for an experiment"""
        
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return {}
        
        results = {}
        control_metrics = None
        
        # Get control group metrics
        control_data = self._get_group_metrics(
            experiment_id, 
            'control'
        )
        control_metrics = self._calculate_metrics(control_data, 'control')
        results['control'] = control_metrics
        
        # Get treatment group metrics
        for group in experiment.treatment_groups:
            group_name = group['name']
            group_data = self._get_group_metrics(experiment_id, group_name)
            
            # Calculate metrics and statistical significance
            treatment_metrics = self._calculate_metrics(group_data, group_name)
            
            # Calculate p-value against control
            if control_metrics and treatment_metrics.users > 30:
                p_value = self._calculate_p_value(
                    control_metrics,
                    treatment_metrics
                )
                treatment_metrics.p_value = p_value
                treatment_metrics.is_significant = p_value < 0.05
            
            results[group_name] = treatment_metrics
        
        return results
    
    def _validate_experiment_config(self, config: ExperimentConfig):
        """Validate experiment configuration"""
        # Check allocation sums to 100%
        total_allocation = sum(config.allocation.values())
        if not (0.99 <= total_allocation <= 1.01):
            raise ValueError(f"Allocation must sum to 100%, got {total_allocation*100}%")
        
        # Ensure control group exists
        if 'control' not in config.allocation:
            raise ValueError("Experiment must have a control group")
    
    def _assign_user_to_variant(
        self,
        user_id: str,
        experiment: ExperimentConfig
    ) -> str:
        """Assign user to experiment variant using consistent hashing"""
        
        # Hash user_id + experiment_id for consistent assignment
        hash_input = f"{user_id}:{experiment.experiment_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # Map to 0-1 range
        assignment_value = (hash_value % 10000) / 10000.0
        
        # Assign based on allocation
        cumulative = 0.0
        for group, allocation in experiment.allocation.items():
            cumulative += allocation
            if assignment_value <= cumulative:
                return group
        
        return 'control'  # Fallback
    
    def _calculate_metrics(
        self,
        data: Dict,
        group: str
    ) -> ExperimentMetrics:
        """Calculate metrics for a group"""
        
        users = data.get('users', 0)
        conversions = data.get('conversions', 0)
        engagement = data.get('engagement', [])
        revenue = data.get('revenue', 0)
        
        # Calculate conversion rate
        conversion_rate = conversions / users if users > 0 else 0
        
        # Calculate confidence interval
        ci = self._calculate_confidence_interval(conversions, users)
        
        # Calculate average engagement
        avg_engagement = np.mean(engagement) if engagement else 0
        
        return ExperimentMetrics(
            group=group,
            users=users,
            conversions=conversions,
            conversion_rate=conversion_rate,
            avg_engagement=avg_engagement,
            revenue=revenue,
            confidence_interval=ci,
            p_value=None,
            is_significant=False
        )
    
    def _calculate_p_value(
        self,
        control: ExperimentMetrics,
        treatment: ExperimentMetrics
    ) -> float:
        """Calculate statistical significance using Chi-square test"""
        
        # Create contingency table
        conversions = [control.conversions, treatment.conversions]
        non_conversions = [
            control.users - control.conversions,
            treatment.users - treatment.conversions
        ]
        
        # Chi-square test
        chi2, p_value, _, _ = stats.chi2_contingency(
            [conversions, non_conversions]
        )
        
        return p_value
    
    def _calculate_confidence_interval(
        self,
        successes: int,
        trials: int,
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for proportion"""
        
        if trials == 0:
            return (0, 0)
        
        proportion = successes / trials
        z_score = stats.norm.ppf((1 + confidence) / 2)
        
        margin = z_score * np.sqrt(
            (proportion * (1 - proportion)) / trials
        )
        
        return (
            max(0, proportion - margin),
            min(1, proportion + margin)
        )
    
    def _get_group_metrics(
        self,
        experiment_id: str,
        group: str
    ) -> Dict:
        """Get raw metrics data for a group"""
        
        # Get from Redis
        key = f"exp_metrics:{experiment_id}:{group}"
        data = self.redis.get(key)
        
        if data:
            return json.loads(data)
        
        return {
            'users': 0,
            'conversions': 0,
            'engagement': [],
            'revenue': 0
        }
    
    def _update_metrics(
        self,
        experiment_id: str,
        variant: str,
        event_type: str,
        value: Optional[float]
    ):
        """Update experiment metrics"""
        
        key = f"exp_metrics:{experiment_id}:{variant}"
        metrics = self._get_group_metrics(experiment_id, variant)
        
        # Update based on event type
        if event_type == 'conversion':
            metrics['conversions'] += 1
            if value:
                metrics['revenue'] += value
        elif event_type == 'engagement':
            metrics['engagement'].append(value or 1.0)
        
        # Save updated metrics
        self.redis.set(key, json.dumps(metrics))
    
    def _get_cached_assignment(
        self,
        user_id: str,
        experiment_id: str
    ) -> Optional[str]:
        """Get cached variant assignment"""
        key = f"exp_assignment:{experiment_id}:{user_id}"
        return self.redis.get(key)
    
    def _cache_assignment(
        self,
        user_id: str,
        experiment_id: str,
        variant: str
    ):
        """Cache variant assignment"""
        key = f"exp_assignment:{experiment_id}:{user_id}"
        self.redis.setex(key, 86400 * 30, variant)  # 30 days
    
    def _track_assignment(
        self,
        user_id: str,
        experiment_id: str,
        variant: str
    ):
        """Track user assignment to variant"""
        
        # Increment user count
        key = f"exp_metrics:{experiment_id}:{variant}"
        metrics = self._get_group_metrics(experiment_id, variant)
        metrics['users'] = metrics.get('users', 0) + 1
        self.redis.set(key, json.dumps(metrics))
    
    def _initialize_metrics(self, experiment_id: str):
        """Initialize metrics storage for experiment"""
        
        experiment = self.experiments[experiment_id]
        
        for group in list(experiment.allocation.keys()):
            key = f"exp_metrics:{experiment_id}:{group}"
            self.redis.set(key, json.dumps({
                'users': 0,
                'conversions': 0,
                'engagement': [],
                'revenue': 0
            }))
    
    def _save_experiment(self, config: ExperimentConfig):
        """Save experiment configuration"""
        key = f"experiment:{config.experiment_id}"
        self.redis.set(key, json.dumps(asdict(config)))
    
    def _load_experiments(self):
        """Load active experiments from Redis"""
        pattern = "experiment:*"
        for key in self.redis.scan_iter(match=pattern):
            data = self.redis.get(key)
            if data:
                exp_dict = json.loads(data)
                exp_dict['status'] = ExperimentStatus(exp_dict['status'])
                config = ExperimentConfig(**exp_dict)
                self.experiments[config.experiment_id] = config