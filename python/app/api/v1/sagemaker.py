"""
SageMaker Infrastructure API Endpoints

Provides REST API for managing SageMaker endpoints, configurations,
and model deployments.

Compatible with Python 3.14.3 and FastAPI 0.115.6
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.auth import get_current_admin
from app.services.sagemaker_service import sagemaker_service

router = APIRouter(
    prefix="/sagemaker", tags=["sagemaker"], dependencies=[Depends(get_current_admin)]
)
# ==================== Request/Response Models ====================


class EndpointConfigRequest(BaseModel):
    """Request model for creating endpoint configuration"""

    config_name: str = Field(..., description="Name for the endpoint configuration")
    model_name: str = Field(..., description="Name of the model to deploy")
    instance_type: str = Field(default="ml.m5.large", description="EC2 instance type")
    initial_instance_count: int = Field(default=1, ge=1, description="Initial number of instances")
    enable_autoscaling: bool = Field(default=True, description="Enable auto-scaling")
    serverless: bool = Field(default=False, description="Use serverless inference")
    serverless_memory_mb: int = Field(default=2048, description="Memory for serverless (MB)")
    serverless_max_concurrency: int = Field(
        default=10, ge=1, le=200, description="Max concurrent invocations"
    )


class MultiModelEndpointConfigRequest(BaseModel):
    """Request model for creating multi-model endpoint configuration"""

    config_name: str = Field(..., description="Name for the endpoint configuration")
    model_name: str = Field(..., description="Name of the multi-model container")
    instance_type: str = Field(default="ml.m5.large", description="EC2 instance type")
    initial_instance_count: int = Field(default=1, ge=1, description="Initial number of instances")


class EndpointRequest(BaseModel):
    """Request model for creating endpoint"""

    endpoint_name: str = Field(..., description="Name for the endpoint")
    config_name: str = Field(..., description="Name of the endpoint configuration")


class AutoScalingRequest(BaseModel):
    """Request model for configuring auto-scaling"""

    endpoint_name: str = Field(..., description="Name of the endpoint")
    variant_name: str = Field(default="AllTraffic", description="Name of the production variant")
    min_capacity: int = Field(default=1, ge=1, description="Minimum number of instances")
    max_capacity: int = Field(default=10, ge=1, description="Maximum number of instances")
    target_invocations_per_instance: int = Field(
        default=1000, ge=1, description="Target invocations per instance"
    )


class ABTestConfigRequest(BaseModel):
    """Request model for creating A/B test endpoint configuration"""

    config_name: str = Field(..., description="Name for the endpoint configuration")
    model_a_name: str = Field(..., description="Name of model A (baseline)")
    model_b_name: str = Field(..., description="Name of model B (challenger)")
    traffic_split_percentage: int = Field(
        default=50, ge=0, le=100, description="Percentage of traffic to model B"
    )
    instance_type: str = Field(default="ml.m5.large", description="EC2 instance type")
    initial_instance_count: int = Field(default=1, ge=1, description="Initial number of instances")


class TrafficSplitRequest(BaseModel):
    """Request model for updating traffic split"""

    endpoint_name: str = Field(..., description="Name of the endpoint")
    model_a_weight: float = Field(..., ge=0.0, le=1.0, description="Weight for model A")
    model_b_weight: float = Field(..., ge=0.0, le=1.0, description="Weight for model B")


class ModelVersionRequest(BaseModel):
    """Request model for creating model version"""

    model_name: str = Field(..., description="Base name for the model")
    model_data_url: str = Field(..., description="S3 URL to model artifacts")
    image_uri: str = Field(..., description="ECR URI for inference container")
    execution_role_arn: str = Field(..., description="IAM role ARN for SageMaker")
    version: str = Field(..., description="Version identifier")


class InferenceRequest(BaseModel):
    """Request model for endpoint inference"""

    endpoint_name: str = Field(..., description="Name of the endpoint")
    payload: Dict[str, Any] = Field(..., description="Input data for inference")
    content_type: str = Field(default="application/json", description="Content type")
    target_variant: Optional[str] = Field(None, description="Specific variant to invoke")


class MultiModelInferenceRequest(BaseModel):
    """Request model for multi-model endpoint inference"""

    endpoint_name: str = Field(..., description="Name of the multi-model endpoint")
    model_name: str = Field(..., description="Name of the specific model")
    payload: Dict[str, Any] = Field(..., description="Input data for inference")
    content_type: str = Field(default="application/json", description="Content type")


# ==================== Endpoint Configuration Endpoints ====================


@router.post("/endpoint-config", response_model=Dict[str, Any])
async def create_endpoint_config(request: EndpointConfigRequest):
    """
    Create SageMaker endpoint configuration with auto-scaling or serverless options.

    - **Standard Endpoint**: Dedicated instances with auto-scaling
    - **Serverless Endpoint**: Pay-per-inference, scales to zero when idle
    """
    try:
        result = await sagemaker_service.create_endpoint_config(
            config_name=request.config_name,
            model_name=request.model_name,
            instance_type=request.instance_type,
            initial_instance_count=request.initial_instance_count,
            enable_autoscaling=request.enable_autoscaling,
            serverless=request.serverless,
            serverless_memory_mb=request.serverless_memory_mb,
            serverless_max_concurrency=request.serverless_max_concurrency,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-model-endpoint-config", response_model=Dict[str, Any])
async def create_multi_model_endpoint_config(request: MultiModelEndpointConfigRequest):
    """
    Create Multi-Model Endpoint configuration for efficient serving of multiple models.

    Multi-Model Endpoints reduce costs by hosting multiple models on the same infrastructure.
    """
    try:
        result = await sagemaker_service.create_multi_model_endpoint_config(
            config_name=request.config_name,
            model_name=request.model_name,
            instance_type=request.instance_type,
            initial_instance_count=request.initial_instance_count,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Endpoint Management Endpoints ====================


@router.post("/endpoint", response_model=Dict[str, Any])
async def create_endpoint(request: EndpointRequest):
    """
    Create SageMaker endpoint from configuration.

    The endpoint will be created asynchronously. Use the wait endpoint to check status.
    """
    try:
        result = await sagemaker_service.create_endpoint(
            endpoint_name=request.endpoint_name, config_name=request.config_name
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/endpoint/{endpoint_name}/wait", response_model=Dict[str, Any])
async def wait_for_endpoint(
    endpoint_name: str, timeout_seconds: int = Query(default=600, ge=60, le=3600)
):
    """
    Wait for endpoint to be in service.

    This is a long-running operation that polls the endpoint status.
    """
    try:
        result = await sagemaker_service.wait_for_endpoint(
            endpoint_name=endpoint_name, timeout_seconds=timeout_seconds
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/endpoint/{endpoint_name}", response_model=Dict[str, Any])
async def update_endpoint(
    endpoint_name: str,
    new_config_name: str = Query(..., description="Name of the new endpoint configuration"),
):
    """
    Update existing endpoint with new configuration.

    This allows zero-downtime model updates and configuration changes.
    """
    try:
        result = await sagemaker_service.update_endpoint(
            endpoint_name=endpoint_name, new_config_name=new_config_name
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/endpoint/{endpoint_name}", response_model=Dict[str, Any])
async def delete_endpoint(endpoint_name: str):
    """
    Delete SageMaker endpoint.

    This will stop all instances and remove the endpoint.
    """
    try:
        result = await sagemaker_service.delete_endpoint(endpoint_name=endpoint_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Auto-Scaling Endpoints ====================


@router.post("/autoscaling", response_model=Dict[str, Any])
async def configure_autoscaling(request: AutoScalingRequest):
    """
    Configure auto-scaling for SageMaker endpoint.

    Auto-scaling adjusts instance count based on invocation rate.
    """
    try:
        result = await sagemaker_service.configure_autoscaling(
            endpoint_name=request.endpoint_name,
            variant_name=request.variant_name,
            min_capacity=request.min_capacity,
            max_capacity=request.max_capacity,
            target_invocations_per_instance=request.target_invocations_per_instance,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== A/B Testing Endpoints ====================


@router.post("/ab-test-config", response_model=Dict[str, Any])
async def create_ab_test_endpoint_config(request: ABTestConfigRequest):
    """
    Create endpoint configuration for A/B testing with traffic splitting.

    Allows testing new models against baseline with controlled traffic distribution.
    """
    try:
        result = await sagemaker_service.create_ab_test_endpoint_config(
            config_name=request.config_name,
            model_a_name=request.model_a_name,
            model_b_name=request.model_b_name,
            traffic_split_percentage=request.traffic_split_percentage,
            instance_type=request.instance_type,
            initial_instance_count=request.initial_instance_count,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/traffic-split", response_model=Dict[str, Any])
async def update_traffic_split(request: TrafficSplitRequest):
    """
    Update traffic split between models in A/B test.

    Allows dynamic adjustment of traffic distribution based on performance.
    """
    try:
        result = await sagemaker_service.update_traffic_split(
            endpoint_name=request.endpoint_name,
            model_a_weight=request.model_a_weight,
            model_b_weight=request.model_b_weight,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Model Versioning Endpoints ====================


@router.post("/model-version", response_model=Dict[str, Any])
async def create_model_version(request: ModelVersionRequest):
    """
    Create a versioned model in SageMaker.

    Enables model versioning for tracking and rollback capabilities.
    """
    try:
        result = await sagemaker_service.create_model_version(
            model_name=request.model_name,
            model_data_url=request.model_data_url,
            image_uri=request.image_uri,
            execution_role_arn=request.execution_role_arn,
            version=request.version,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-versions/{base_model_name}", response_model=List[Dict[str, Any]])
async def list_model_versions(base_model_name: str):
    """
    List all versions of a model.

    Returns all versions sorted by creation time (newest first).
    """
    try:
        result = await sagemaker_service.list_model_versions(base_model_name=base_model_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Inference Endpoints ====================


@router.post("/invoke", response_model=Dict[str, Any])
async def invoke_endpoint(request: InferenceRequest):
    """
    Invoke SageMaker endpoint for inference.

    Sends input data to the endpoint and returns predictions.
    """
    try:
        result = await sagemaker_service.invoke_endpoint(
            endpoint_name=request.endpoint_name,
            payload=request.payload,
            content_type=request.content_type,
            target_variant=request.target_variant,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoke-multi-model", response_model=Dict[str, Any])
async def invoke_multi_model_endpoint(request: MultiModelInferenceRequest):
    """
    Invoke specific model on Multi-Model Endpoint.

    Allows targeting a specific model on a multi-model endpoint.
    """
    try:
        result = await sagemaker_service.invoke_multi_model_endpoint(
            endpoint_name=request.endpoint_name,
            model_name=request.model_name,
            payload=request.payload,
            content_type=request.content_type,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Monitoring Endpoints ====================


@router.get("/metrics/{endpoint_name}", response_model=Dict[str, Any])
async def get_endpoint_metrics(
    endpoint_name: str,
    metric_name: Literal[
        "ModelLatency", "Invocations", "InvocationsPerInstance", "ModelSetupTime", "OverheadLatency"
    ] = Query(..., description="Name of the metric to retrieve"),
    hours_back: int = Query(default=1, ge=1, le=168, description="Hours of historical data"),
    period_seconds: int = Query(
        default=300, ge=60, le=3600, description="Metric aggregation period"
    ),
):
    """
    Get CloudWatch metrics for SageMaker endpoint.

    Retrieves performance metrics for monitoring and analysis.
    """
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)

        result = await sagemaker_service.get_endpoint_metrics(
            endpoint_name=endpoint_name,
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            period_seconds=period_seconds,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
