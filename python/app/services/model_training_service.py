"""
Model Training Service for Custom Crop Yield Prediction Models

Collects and prepares training data from farmer outcomes (actual yields, harvest dates)
Trains custom models for 92-95% accuracy (vs 85-90% Bedrock baseline)
Implements model evaluation and validation with cross-validation and test sets
Deploys models to SageMaker endpoints with monitoring and logging

Compatible with Python 3.14.3, scikit-learn, pandas, numpy
"""

import json
import logging
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.database import get_async_db_context
from app.orm.crop import Crop
from app.orm.farm import Farm
from app.orm.farm_plot import FarmPlot
from app.services.sagemaker_service import sagemaker_service

logger = logging.getLogger(__name__)

try:
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import KFold, cross_val_score, train_test_split
    from sklearn.preprocessing import LabelEncoder, StandardScaler

    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    # Stub for type hints and to prevent NameError
    pd = Any
    np = Any

    class StandardScaler:
        pass

    class LabelEncoder:
        pass

    class RandomForestRegressor:
        pass

    class GradientBoostingRegressor:
        pass

    logger.warning(
        "Local ML libraries (pandas, sklearn) not found. ModelTrainingService will be disabled."
    )


class ModelTrainingService:
    """Service for training custom crop yield prediction models"""

    def __init__(self):
        """Initialize model training service"""
        from google.cloud import storage

        try:
            self.gcs_client = storage.Client()
        except Exception as e:
            logger.warning(
                f"Google Cloud Storage client initialization failed: {e}. GCS will run in fallback/mock mode."
            )
            self.gcs_client = None

        self.s3_client = None  # Retained for unit test compatibility
        self.model_bucket = getattr(settings, "GCS_BUCKET", "cropsense-uploads")
        if HAS_ML_LIBS:
            self.scaler = StandardScaler()
            self.label_encoders = {}
        else:
            self.scaler = None
            self.label_encoders = {}

    # ==================== Data Collection ====================

    async def collect_training_data(
        self, min_samples: int = 100, include_incomplete: bool = False
    ) -> "pd.DataFrame":
        """
        Collect training data from farmer outcomes (actual yields, harvest dates).

        Args:
            min_samples: Minimum number of samples required for training
            include_incomplete: Include crops without actual yield data

        Returns:
            DataFrame with training features and targets
        """
        if not HAS_ML_LIBS:
            raise ImportError("Local ML libraries not found. Data collection disabled.")
        async with get_async_db_context() as session:
            # Query crops with actual outcomes
            query = session.query(Crop).join(FarmPlot).join(Farm)

            if not include_incomplete:
                # Only include crops with actual yield data
                query = query.filter(Crop.actual_yield.isnot(None))

            crops = query.all()

            if len(crops) < min_samples:
                raise ValueError(
                    f"Insufficient training data: {len(crops)} samples "
                    f"(minimum {min_samples} required)"
                )

            # Extract features and targets
            data = []
            for crop in crops:
                farm_plot = crop.farm_plot
                farm = farm_plot.farm

                # Calculate days from planting to harvest
                if crop.expected_harvest_date and crop.planting_date:
                    days_to_harvest = (crop.expected_harvest_date - crop.planting_date).days
                else:
                    days_to_harvest = None

                record = {
                    # Target variables
                    "actual_yield": crop.actual_yield,
                    "actual_profit": crop.actual_profit,
                    # Crop features
                    "crop_name": crop.crop_name,
                    "crop_variety": crop.crop_variety,
                    "season": crop.season,
                    "area": crop.area,
                    "planting_date": crop.planting_date,
                    "expected_harvest_date": crop.expected_harvest_date,
                    "days_to_harvest": days_to_harvest,
                    # Farm features
                    "state": farm.state,
                    "district": farm.district,
                    "soil_type": farm.soil_type,
                    "irrigation_type": farm.irrigation_type,
                    "total_area": farm.total_area,
                    # Plot features
                    "plot_area": farm_plot.area,
                    "plot_soil_type": farm_plot.soil_type,
                    # Temporal features
                    "planting_month": crop.planting_date.month if crop.planting_date else None,
                    "planting_year": crop.planting_date.year if crop.planting_date else None,
                }

                data.append(record)

            df = pd.DataFrame(data)
            return df

    # ==================== Data Preparation ====================

    def prepare_features(
        self,
    ) -> Tuple["pd.DataFrame", "pd.Series"]:
        """
        Prepare features for model training with encoding and scaling.

        Args:
            df: Raw training data
            target_column: Name of the target variable column

        Returns:
            Tuple of (features DataFrame, target Series)
        """
        # Drop rows with missing target values
        df_clean = df.dropna(subset=[target_column]).copy()

        # Separate features and target
        target = df_clean[target_column]
        features = df_clean.drop(columns=["actual_yield", "actual_profit"], errors="ignore")

        # Encode categorical variables
        categorical_cols = [
            "crop_name",
            "crop_variety",
            "season",
            "state",
            "district",
            "soil_type",
            "irrigation_type",
            "plot_soil_type",
        ]

        for col in categorical_cols:
            if col in features.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    features[col] = self.label_encoders[col].fit_transform(
                        features[col].fillna("unknown")
                    )
                else:
                    # Handle unseen categories
                    features[col] = features[col].fillna("unknown")
                    features[col] = features[col].apply(
                        lambda x: x if x in self.label_encoders[col].classes_ else "unknown"
                    )
                    features[col] = self.label_encoders[col].transform(features[col])

        # Handle date columns
        date_cols = ["planting_date", "expected_harvest_date"]
        for col in date_cols:
            if col in features.columns:
                features = features.drop(columns=[col])

        # Separate categorical and numeric columns
        categorical_encoded_cols = [col for col in categorical_cols if col in features.columns]
        numeric_cols = [
            col
            for col in features.select_dtypes(include=[np.number]).columns
            if col not in categorical_encoded_cols
        ]

        # Fill missing numeric values with median
        for col in numeric_cols:
            if features[col].isnull().any():
                features[col] = features[col].fillna(features[col].median())

        # Scale only numeric features (not categorical encoded ones)
        if numeric_cols:
            features[numeric_cols] = self.scaler.fit_transform(features[numeric_cols])

        return features, target

    # ==================== Model Training ====================

    async def train_yield_prediction_model(
        self, test_size: float = 0.2, random_state: int = 42, n_cv_folds: int = 5
    ) -> Dict[str, Any]:
        """
        Train custom crop yield prediction model with cross-validation.
        Target: 92-95% accuracy (vs 85-90% Bedrock baseline)

        Args:
            test_size: Proportion of data for testing
            random_state: Random seed for reproducibility
            n_cv_folds: Number of cross-validation folds

        Returns:
            Dict with model performance metrics and model artifacts
        """
        # Collect training data
        df = await self.collect_training_data(min_samples=100)

        # Prepare features
        X, y = self.prepare_features(df, target_column="actual_yield")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        # Train ensemble of models
        models = {
            "random_forest": RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=random_state,
                n_jobs=-1,
            ),
            "gradient_boosting": GradientBoostingRegressor(
                n_estimators=200,
                max_depth=7,
                learning_rate=0.1,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=random_state,
            ),
        }

        results = {}
        best_model_name = None
        best_model_obj = None
        best_score = -float("inf")  # Start with negative infinity

        for model_name, model in models.items():
            # Train model
            model.fit(X_train, y_train)

            # Cross-validation
            cv_scores = cross_val_score(
                model,
                X_train,
                y_train,
                cv=KFold(n_splits=n_cv_folds, shuffle=True, random_state=random_state),
                scoring="r2",
                n_jobs=-1,
            )

            # Test set evaluation
            y_pred = model.predict(X_test)

            # Calculate metrics
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)

            # Calculate accuracy (within 10% of actual)
            accuracy = np.mean(np.abs(y_pred - y_test) / y_test <= 0.10) * 100

            results[model_name] = {
                "cv_scores": cv_scores.tolist(),
                "cv_mean": float(cv_scores.mean()),
                "cv_std": float(cv_scores.std()),
                "test_mae": float(mae),
                "test_rmse": float(rmse),
                "test_r2": float(r2),
                "test_accuracy": float(accuracy),
                "n_train_samples": len(X_train),
                "n_test_samples": len(X_test),
            }

            # Track best model
            if r2 > best_score:
                best_score = r2
                best_model_name = model_name
                best_model_obj = model

        # Ensure we have a best model
        if best_model_name is None:
            # Fallback to first model if none selected
            best_model_name = list(models.keys())[0]
            best_model_obj = models[best_model_name]

        # Save best model
        model_path = await self._save_model(best_model_obj, best_model_name, "yield_prediction")

        return {
            "best_model": best_model_name,
            "model_path": model_path,
            "results": results,
            "target_accuracy": "92-95%",
            "achieved_accuracy": f"{results[best_model_name]['test_accuracy']:.2f}%",
            "meets_target": results[best_model_name]["test_accuracy"] >= 92.0,
            "training_date": datetime.now(UTC).isoformat(),
        }

    # ==================== Model Evaluation ====================

    def evaluate_model(
        self, model: Any, X_test: "pd.DataFrame", y_test: "pd.Series"
    ) -> Dict[str, Any]:
        """
        Comprehensive model evaluation with multiple metrics.

        Args:
            model: Trained model
            X_test: Test features
            y_test: Test targets

        Returns:
            Dict with evaluation metrics
        """
        y_pred = model.predict(X_test)

        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        # Accuracy within different thresholds
        accuracy_5pct = np.mean(np.abs(y_pred - y_test) / y_test <= 0.05) * 100
        accuracy_10pct = np.mean(np.abs(y_pred - y_test) / y_test <= 0.10) * 100
        accuracy_15pct = np.mean(np.abs(y_pred - y_test) / y_test <= 0.15) * 100

        # Prediction errors
        errors = y_pred - y_test

        return {
            "mae": float(mae),
            "rmse": float(rmse),
            "r2_score": float(r2),
            "accuracy_within_5pct": float(accuracy_5pct),
            "accuracy_within_10pct": float(accuracy_10pct),
            "accuracy_within_15pct": float(accuracy_15pct),
            "mean_error": float(errors.mean()),
            "std_error": float(errors.std()),
            "min_error": float(errors.min()),
            "max_error": float(errors.max()),
            "n_samples": len(y_test),
        }

    # ==================== Model Persistence ====================

    async def _save_model(self, model: Any, model_name: str, model_type: str) -> str:
        """
        Save trained model to S3 for SageMaker deployment.

        Args:
            model: Trained model
            model_name: Name of the model
            model_type: Type of model (yield_prediction, profit_prediction)

        Returns:
            S3 path to saved model
        """
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save model artifacts
            model_file = os.path.join(tmpdir, "model.joblib")
            scaler_file = os.path.join(tmpdir, "scaler.joblib")
            encoders_file = os.path.join(tmpdir, "encoders.joblib")

            joblib.dump(model, model_file)
            joblib.dump(self.scaler, scaler_file)
            joblib.dump(self.label_encoders, encoders_file)

            # Create model metadata
            metadata = {
                "model_name": model_name,
                "model_type": model_type,
                "created_at": datetime.now(UTC).isoformat(),
                "framework": "scikit-learn",
                "python_version": "3.14.3",
            }

            metadata_file = os.path.join(tmpdir, "metadata.json")
            with open(metadata_file, "w") as f:
                json.dump(metadata, f)

            # Create tar.gz archive
            import tarfile

            archive_path = os.path.join(tmpdir, "model.tar.gz")
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(model_file, arcname="model.joblib")
                tar.add(scaler_file, arcname="scaler.joblib")
                tar.add(encoders_file, arcname="encoders.joblib")
                tar.add(metadata_file, arcname="metadata.json")

            # Upload to GCS
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            gcs_key = f"models/{model_type}/{model_name}_{timestamp}/model.tar.gz"

            if self.gcs_client:
                try:
                    bucket = self.gcs_client.bucket(self.model_bucket)
                    blob = bucket.blob(gcs_key)
                    blob.upload_from_filename(archive_path)
                    logger.info(
                        f"Model successfully uploaded to GCS at gs://{self.model_bucket}/{gcs_key}"
                    )
                except Exception as e:
                    logger.error(f"Failed to upload model to GCS: {e}")

            gcs_path = f"gs://{self.model_bucket}/{gcs_key}"
            return gcs_path

    async def load_model(self, s3_path: str) -> Tuple[Any, "StandardScaler", Dict]:
        """
        Load trained model from GCS (supports s3:// or gs:// path format).

        Args:
            s3_path: Cloud path to model artifacts

        Returns:
            Tuple of (model, scaler, label_encoders)
        """
        # Parse path (works for gs://... or s3://...)
        bucket_name = s3_path.split("/")[2]
        key = "/".join(s3_path.split("/")[3:])

        with tempfile.TemporaryDirectory() as tmpdir:
            # Download from GCS
            archive_path = os.path.join(tmpdir, "model.tar.gz")

            if self.gcs_client:
                try:
                    bucket = self.gcs_client.bucket(bucket_name)
                    blob = bucket.blob(key)
                    blob.download_to_filename(archive_path)
                except Exception as e:
                    logger.error(f"Failed to download model from GCS: {e}")
                    raise
            else:
                # Fallback: create mock/empty archive if GCS not configured in dev
                import tarfile

                with tarfile.open(archive_path, "w:gz") as tar:
                    # Create empty files
                    for f in ["model.joblib", "scaler.joblib", "encoders.joblib"]:
                        p = os.path.join(tmpdir, f)
                        with open(p, "w") as fh:
                            fh.write("")
                        tar.add(p, arcname=f)

            # Extract archive
            import tarfile

            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(tmpdir)

            # Load artifacts
            try:
                model = joblib.load(os.path.join(tmpdir, "model.joblib"))
                scaler = joblib.load(os.path.join(tmpdir, "scaler.joblib"))
                encoders = joblib.load(os.path.join(tmpdir, "encoders.joblib"))
            except Exception as e:
                logger.warning(
                    f"Failed to load joblib files (expected in local dev fallbacks): {e}"
                )
                # Mock return
                model = None
                scaler = None
                encoders = {}

            return model, scaler, encoders

    # ==================== SageMaker Deployment ====================

    async def deploy_to_sagemaker(
        self,
        model_s3_path: str,
        endpoint_name: str,
        instance_type: str = "ml.m5.large",
        serverless: bool = True,
    ) -> Dict[str, Any]:
        """
        Deploy trained model to SageMaker endpoint.

        Args:
            model_s3_path: S3 path to model artifacts
            endpoint_name: Name for the endpoint
            instance_type: EC2 instance type (ignored if serverless=True)
            serverless: Use SageMaker Serverless Inference

        Returns:
            Dict with deployment details
        """
        # Get SageMaker execution role
        execution_role = settings.SAGEMAKER_EXECUTION_ROLE_ARN

        # Get scikit-learn container image
        image_uri = self._get_sklearn_image_uri()

        # Create model version
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        model_name = f"crop-yield-model-{timestamp}"

        model_result = await sagemaker_service.create_model_version(
            model_name=model_name,
            model_data_url=model_s3_path,
            image_uri=image_uri,
            execution_role_arn=execution_role,
            version=timestamp,
        )

        # Create endpoint configuration
        config_name = f"{endpoint_name}-config-{timestamp}"

        if serverless:
            config_result = await sagemaker_service.create_endpoint_config(
                config_name=config_name,
                model_name=model_result["model_name"],
                serverless=True,
                serverless_memory_mb=4096,
                serverless_max_concurrency=20,
            )
        else:
            config_result = await sagemaker_service.create_endpoint_config(
                config_name=config_name,
                model_name=model_result["model_name"],
                instance_type=instance_type,
                initial_instance_count=1,
                enable_autoscaling=True,
            )

        # Create or update endpoint
        try:
            endpoint_result = await sagemaker_service.create_endpoint(
                endpoint_name=endpoint_name, config_name=config_name
            )
        except Exception as e:
            if "already exists" in str(e).lower():
                # Update existing endpoint
                endpoint_result = await sagemaker_service.update_endpoint(
                    endpoint_name=endpoint_name, new_config_name=config_name
                )
            else:
                raise

        # Wait for endpoint to be in service
        await sagemaker_service.wait_for_endpoint(endpoint_name, timeout_seconds=600)

        return {
            "endpoint_name": endpoint_name,
            "model_name": model_result["model_name"],
            "config_name": config_name,
            "serverless": serverless,
            "status": "deployed",
            "deployment_time": datetime.now(UTC).isoformat(),
        }

    def _get_sklearn_image_uri(self) -> str:
        """Get scikit-learn container image URI for SageMaker"""
        # SageMaker scikit-learn container
        region = settings.AWS_REGION
        account_id = "683313688378"  # SageMaker account for us-east-1

        # Map regions to account IDs
        region_accounts = {
            "us-east-1": "683313688378",
            "us-east-2": "257758044811",
            "us-west-1": "746614075791",
            "us-west-2": "246618743249",
            "ap-south-1": "720646828776",
            "ap-southeast-1": "121021644041",
            "ap-southeast-2": "783357654285",
            "eu-west-1": "141502667606",
            "eu-central-1": "492215442770",
        }

        account_id = region_accounts.get(region, account_id)

        return f"{account_id}.dkr.ecr.{region}.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3"


# Singleton instance
model_training_service = ModelTrainingService()
