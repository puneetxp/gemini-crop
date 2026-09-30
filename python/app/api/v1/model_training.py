"""
Model Training API Endpoints

Provides endpoints for training custom crop yield prediction models
and deploying them to SageMaker endpoints.

Compatible with Python 3.14.3 and FastAPI 0.115.6
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import get_current_admin
from app.services.model_training_service import model_training_service

router = APIRouter(
    prefix="/model-training", tags=["model-training"], dependencies=[Depends(get_current_admin)]
)
# ==================== Request/Response Models ====================


class TrainModelRequest(BaseModel):
    """Request model for training a new model"""

    test_size: float = Field(default=0.2, ge=0.1, le=0.5, description="Test set proportion")
    n_cv_folds: int = Field(default=5, ge=3, le=10, description="Cross-validation folds")
    random_state: int = Field(default=42, description="Random seed for reproducibility")


class DeployModelRequest(BaseModel):
    """Request model for deploying a model to SageMaker"""

    model_s3_path: str = Field(..., description="S3 path to model artifacts")
    endpoint_name: str = Field(..., description="Name for the SageMaker endpoint")
    instance_type: str = Field(default="ml.m5.large", description="EC2 instance type")
    serverless: bool = Field(default=True, description="Use Serverless Inference")


class TrainingDataStatsResponse(BaseModel):
    """Response model for training data statistics"""

    total_samples: int
    samples_with_yield: int
    samples_with_profit: int
    unique_crops: int
    unique_states: int
    unique_districts: int
    date_range: Dict[str, str]


# ==================== Endpoints ====================


@router.get("/data-stats", response_model=TrainingDataStatsResponse)
async def get_training_data_stats():
    """
    Get statistics about available training data.

    Returns:
        Statistics about training data samples
    """
    try:
        df = await model_training_service.collect_training_data(
            min_samples=1, include_incomplete=True
        )

        stats = {
            "total_samples": len(df),
            "samples_with_yield": df["actual_yield"].notna().sum(),
            "samples_with_profit": df["actual_profit"].notna().sum(),
            "unique_crops": df["crop_name"].nunique(),
            "unique_states": df["state"].nunique(),
            "unique_districts": df["district"].nunique(),
            "date_range": {
                "earliest": (
                    df["planting_date"].min().isoformat()
                    if df["planting_date"].notna().any()
                    else None
                ),
                "latest": (
                    df["planting_date"].max().isoformat()
                    if df["planting_date"].notna().any()
                    else None
                ),
            },
        }

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get training data stats: {str(e)}")


@router.post("/train-yield-model")
async def train_yield_prediction_model(
    request: TrainModelRequest, background_tasks: BackgroundTasks
):
    """
    Train custom crop yield prediction model.
    Target: 92-95% accuracy (vs 85-90% Bedrock baseline)

    Args:
        request: Training configuration
        background_tasks: FastAPI background tasks

    Returns:
        Training results with model performance metrics
    """
    try:
        # Train model
        result = await model_training_service.train_yield_prediction_model(
            test_size=request.test_size,
            random_state=request.random_state,
            n_cv_folds=request.n_cv_folds,
        )

        return {"status": "success", "message": "Model training completed", "result": result}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")


@router.post("/deploy-model")
async def deploy_model_to_sagemaker(request: DeployModelRequest):
    """
    Deploy trained model to SageMaker endpoint.

    Args:
        request: Deployment configuration

    Returns:
        Deployment details
    """
    try:
        result = await model_training_service.deploy_to_sagemaker(
            model_s3_path=request.model_s3_path,
            endpoint_name=request.endpoint_name,
            instance_type=request.instance_type,
            serverless=request.serverless,
        )

        return {"status": "success", "message": "Model deployed to SageMaker", "result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model deployment failed: {str(e)}")


@router.get("/model-versions/{model_type}")
async def list_model_versions(model_type: str):
    """
    List all versions of a model type.

    Args:
        model_type: Type of model (yield_prediction, profit_prediction)

    Returns:
        List of model versions
    """
    try:
        # List models from S3
        response = model_training_service.s3_client.list_objects_v2(
            Bucket=model_training_service.model_bucket, Prefix=f"models/{model_type}/"
        )

        versions = []
        for obj in response.get("Contents", []):
            if obj["Key"].endswith("model.tar.gz"):
                versions.append(
                    {
                        "s3_path": f"s3://{model_training_service.model_bucket}/{obj['Key']}",
                        "size_mb": obj["Size"] / (1024 * 1024),
                        "last_modified": obj["LastModified"].isoformat(),
                    }
                )

        return {"model_type": model_type, "versions": versions, "total_versions": len(versions)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list model versions: {str(e)}")
