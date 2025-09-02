"""
Unit tests for A/B Testing Framework
File: tests/phase3/test_ab_testing.py
"""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.ml_service.app.core.ab_testing import (
    ABTestingFramework,
    ExperimentConfig,
    ExperimentStatus,
    ExperimentMetrics
)


class TestABTestingFramework:
    
    @pytest.fixture
    def redis_mock(self):
        """Mock Redis client"""
        mock = Mock()
        mock.get.return_value = None
        mock.set.return_value = True
        mock.setex.return_value = True
        mock.scan_iter.return_value = []
        return mock
    
    @pytest.fixture
    def ab_framework(self, redis_mock):
        """Create ABTestingFramework instance"""
        return ABTestingFramework(redis_mock)
    
    @pytest.fixture
    def sample_experiment(self):
        """Sample experiment configuration"""
        return ExperimentConfig(
            experiment_id="test_exp_001",
            name="Test Experiment",
            description="Testing A/B framework",
            start_date=datetime.utcnow().isoformat(),
            end_date=None,
            status=ExperimentStatus.DRAFT,
            control_group={'algorithm': 'standard'},
            treatment_groups=[
                {'name': 'variant_a', 'algorithm': 'enhanced'}
            ],
            metrics=['conversion', 'engagement'],
            target_sample_size=1000,
            allocation={'control': 0.5, 'variant_a': 0.5},
            metadata=None
        )
    
    def test_create_experiment(self, ab_framework, sample_experiment):
        """Test experiment creation"""
        exp_id = ab_framework.create_experiment(sample_experiment)
        
        assert exp_id == "test_exp_001"
        assert exp_id in ab_framework.experiments
        assert ab_framework.experiments[exp_id].name == "Test Experiment"
    
    def test_validate_experiment_allocation(self, ab_framework):
        """Test allocation validation"""
        invalid_config = ExperimentConfig(
            experiment_id="invalid",
            name="Invalid",
            description="Invalid allocation",
            start_date=datetime.utcnow().isoformat(),
            end_date=None,
            status=ExperimentStatus.DRAFT,
            control_group={'algorithm': 'standard'},
            treatment_groups=[],
            metrics=[],
            target_sample_size=None,
            allocation={'control': 0.3, 'variant': 0.3},  # Doesn't sum to 1
            metadata=None
        )
        
        with pytest.raises(ValueError):
            ab_framework.create_experiment(invalid_config)
    
    def test_user_variant_assignment(self, ab_framework, sample_experiment):
        """Test consistent user variant assignment"""
        sample_experiment.status = ExperimentStatus.RUNNING
        ab_framework.experiments[sample_experiment.experiment_id] = sample_experiment
        
        # Same user should get same variant
        variant1 = ab_framework.get_user_variant("user123", "test_exp_001")
        variant2 = ab_framework.get_user_variant("user123", "test_exp_001")
        
        assert variant1 == variant2
        assert variant1 in ['control', 'variant_a']
    
    def test_variant_distribution(self, ab_framework, sample_experiment):
        """Test that variant assignment follows allocation"""
        sample_experiment.status = ExperimentStatus.RUNNING
        ab_framework.experiments[sample_experiment.experiment_id] = sample_experiment
        
        assignments = {'control': 0, 'variant_a': 0}
        
        # Assign 1000 users
        for i in range(1000):
            variant = ab_framework._assign_user_to_variant(
                f"user_{i}",
                sample_experiment
            )
            assignments[variant] += 1
        
        # Check distribution is roughly 50/50 (with 5% tolerance)
        control_ratio = assignments['control'] / 1000
        assert 0.45 <= control_ratio <= 0.55
    
    def test_track_event(self, ab_framework, sample_experiment, redis_mock):
        """Test event tracking"""
        sample_experiment.status = ExperimentStatus.RUNNING
        ab_framework.experiments[sample_experiment.experiment_id] = sample_experiment
        
        ab_framework.track_event(
            user_id="user123",
            experiment_id="test_exp_001",
            event_type="conversion",
            value=99.99,
            metadata={'item': 'product_123'}
        )
        
        # Verify Redis was called
        assert redis_mock.rpush.called
        assert redis_mock.get.called
    
    def test_calculate_metrics(self, ab_framework):
        """Test metrics calculation"""
        data = {
            'users': 1000,
            'conversions': 50,
            'engagement': [1, 2, 3, 4, 5],
            'revenue': 5000
        }
        
        metrics = ab_framework._calculate_metrics(data, 'control')
        
        assert metrics.users == 1000
        assert metrics.conversions == 50
        assert metrics.conversion_rate == 0.05
        assert metrics.avg_engagement == 3.0
        assert metrics.revenue == 5000
    
    def test_confidence_interval(self, ab_framework):
        """Test confidence interval calculation"""
        ci = ab_framework._calculate_confidence_interval(50, 1000)
        
        # 5% conversion rate
        assert 0.035 < ci[0] < 0.040  # Lower bound
        assert 0.060 < ci[1] < 0.065  # Upper bound
    
    def test_p_value_calculation(self, ab_framework):
        """Test statistical significance calculation"""
        control = ExperimentMetrics(
            group='control',
            users=1000,
            conversions=50,
            conversion_rate=0.05,
            avg_engagement=3.0,
            revenue=5000,
            confidence_interval=(0.037, 0.063),
            p_value=None,
            is_significant=False
        )
        
        treatment = ExperimentMetrics(
            group='variant_a',
            users=1000,
            conversions=70,
            conversion_rate=0.07,
            avg_engagement=3.5,
            revenue=7000,
            confidence_interval=(0.055, 0.085),
            p_value=None,
            is_significant=False
        )
        
        p_value = ab_framework._calculate_p_value(control, treatment)
        
        # Should detect significance for 5% vs 7% conversion
        assert p_value < 0.05
    
    def test_experiment_results(self, ab_framework, sample_experiment, redis_mock):
        """Test getting experiment results"""
        sample_experiment.status = ExperimentStatus.RUNNING
        ab_framework.experiments[sample_experiment.experiment_id] = sample_experiment
        
        # Mock metrics data
        redis_mock.get.side_effect = [
            json.dumps({
                'users': 500,
                'conversions': 25,
                'engagement': [1, 2, 3],
                'revenue': 2500
            }),
            json.dumps({
                'users': 500,
                'conversions': 35,
                'engagement': [2, 3, 4],
                'revenue': 3500
            })
        ]
        
        results = ab_framework.get_experiment_results("test_exp_001")
        
        assert 'control' in results
        assert 'variant_a' in results
        assert results['control'].conversion_rate == 0.05
        assert results['variant_a'].conversion_rate == 0.07


if __name__ == "__main__":
    pytest.main([__file__, "-v"])