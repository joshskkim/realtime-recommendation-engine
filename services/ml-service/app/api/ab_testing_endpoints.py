"""
A/B Testing API endpoints for ML Service
File: services/ml-service/app/api/ab_testing_endpoints.py
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
import redis
from app.core.ab_testing import (
    ABTestingFramework,
    ExperimentConfig,
    ExperimentStatus
)

router = APIRouter(prefix="/experiments", tags=["A/B Testing"])

# Initialize A/B testing framework
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
ab_framework = ABTestingFramework(redis_client)


class CreateExperimentRequest(BaseModel):
    name: str
    description: str
    control_algorithm: str
    treatment_algorithms: List[Dict[str, str]]
    allocation: Dict[str, float]
    metrics: List[str]
    target_sample_size: Optional[int] = None
    duration_days: Optional[int] = 30


class AssignmentRequest(BaseModel):
    user_id: str
    experiment_id: str


class TrackEventRequest(BaseModel):
    user_id: str
    experiment_id: str
    event_type: str
    value: Optional[float] = None
    metadata: Optional[Dict] = None


@router.post("/create")
async def create_experiment(request: CreateExperimentRequest):
    """Create a new A/B test experiment"""
    
    experiment_id = f"exp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    config = ExperimentConfig(
        experiment_id=experiment_id,
        name=request.name,
        description=request.description,
        start_date=datetime.utcnow().isoformat(),
        end_date=None,
        status=ExperimentStatus.DRAFT,
        control_group={'algorithm': request.control_algorithm},
        treatment_groups=request.treatment_algorithms,
        metrics=request.metrics,
        target_sample_size=request.target_sample_size,
        allocation=request.allocation,
        metadata=None
    )
    
    try:
        ab_framework.create_experiment(config)
        return {
            "experiment_id": experiment_id,
            "status": "created",
            "message": f"Experiment '{request.name}' created successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/start/{experiment_id}")
async def start_experiment(experiment_id: str):
    """Start an experiment"""
    
    experiment = ab_framework.experiments.get(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    experiment.status = ExperimentStatus.RUNNING
    ab_framework._save_experiment(experiment)
    
    return {
        "experiment_id": experiment_id,
        "status": "running",
        "message": "Experiment started"
    }


@router.post("/stop/{experiment_id}")
async def stop_experiment(experiment_id: str):
    """Stop an experiment"""
    
    experiment = ab_framework.experiments.get(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    experiment.status = ExperimentStatus.COMPLETED
    experiment.end_date = datetime.utcnow().isoformat()
    ab_framework._save_experiment(experiment)
    
    return {
        "experiment_id": experiment_id,
        "status": "completed",
        "message": "Experiment stopped"
    }


@router.get("/assignment")
async def get_user_assignment(user_id: str, experiment_id: str):
    """Get user's variant assignment for an experiment"""
    
    variant = ab_framework.get_user_variant(user_id, experiment_id)
    
    if not variant:
        raise HTTPException(
            status_code=404, 
            detail="Experiment not found or not running"
        )
    
    return {
        "user_id": user_id,
        "experiment_id": experiment_id,
        "variant": variant
    }


@router.post("/track")
async def track_event(request: TrackEventRequest):
    """Track user event for experiment"""
    
    ab_framework.track_event(
        user_id=request.user_id,
        experiment_id=request.experiment_id,
        event_type=request.event_type,
        value=request.value,
        metadata=request.metadata
    )
    
    return {
        "status": "tracked",
        "message": f"Event '{request.event_type}' tracked for user {request.user_id}"
    }


@router.get("/results/{experiment_id}")
async def get_experiment_results(experiment_id: str):
    """Get current results for an experiment"""
    
    results = ab_framework.get_experiment_results(experiment_id)
    
    if not results:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    # Format results for API response
    formatted_results = {}
    for group, metrics in results.items():
        formatted_results[group] = {
            "users": metrics.users,
            "conversions": metrics.conversions,
            "conversion_rate": round(metrics.conversion_rate, 4),
            "avg_engagement": round(metrics.avg_engagement, 2),
            "revenue": round(metrics.revenue, 2),
            "confidence_interval": [
                round(metrics.confidence_interval[0], 4),
                round(metrics.confidence_interval[1], 4)
            ],
            "p_value": round(metrics.p_value, 4) if metrics.p_value else None,
            "is_significant": metrics.is_significant
        }
    
    return {
        "experiment_id": experiment_id,
        "results": formatted_results,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/list")
async def list_experiments(status: Optional[str] = None):
    """List all experiments"""
    
    experiments = []
    for exp_id, config in ab_framework.experiments.items():
        if status and config.status.value != status:
            continue
            
        experiments.append({
            "experiment_id": exp_id,
            "name": config.name,
            "status": config.status.value,
            "start_date": config.start_date,
            "end_date": config.end_date
        })
    
    return {
        "experiments": experiments,
        "total": len(experiments)
    }


@router.get("/recommendations/{user_id}")
async def get_ab_tested_recommendations(user_id: str, limit: int = 10):
    """Get recommendations with A/B testing applied"""
    
    # Find active experiments
    active_experiments = [
        exp for exp in ab_framework.experiments.values()
        if exp.status == ExperimentStatus.RUNNING
    ]
    
    if not active_experiments:
        # No active experiments, return standard recommendations
        return {
            "user_id": user_id,
            "variant": "control",
            "strategy": "standard",
            "recommendations": []  # Would call standard rec engine
        }
    
    # Get user's variant for first active experiment
    experiment = active_experiments[0]
    variant = ab_framework.get_user_variant(user_id, experiment.experiment_id)
    
    # Get recommendations based on variant
    if variant == "control":
        strategy = experiment.control_group.get('algorithm', 'standard')
    else:
        # Find treatment group config
        treatment = next(
            (t for t in experiment.treatment_groups if t['name'] == variant),
            None
        )
        strategy = treatment.get('algorithm', 'standard') if treatment else 'standard'
    
    # Would call actual recommendation engine with strategy
    # For now, return mock response
    return {
        "user_id": user_id,
        "experiment_id": experiment.experiment_id,
        "variant": variant,
        "strategy": strategy,
        "recommendations": [f"item_{i}_{strategy}" for i in range(limit)]
    }