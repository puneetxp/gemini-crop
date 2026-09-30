"""
Model Router - Intelligent routing logic for hybrid AI system

Determines which model (SageMaker or Bedrock) to use based on:
- Query type and complexity
- Data availability
- Model performance history
- Cost constraints

Compatible with Python 3.14.3
"""

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """Routing strategies for model selection"""

    ACCURACY_FIRST = "accuracy_first"  # Prioritize accuracy (use SageMaker when possible)
    COST_FIRST = "cost_first"  # Prioritize cost (use SageMaker for batch, Bedrock for single)
    BALANCED = "balanced"  # Balance accuracy and cost
    FALLBACK_ONLY = "fallback_only"  # Use Bedrock only, SageMaker as fallback


class ModelRouter:
    """
    Intelligent router for hybrid AI system.

    Routes queries to optimal model based on multiple factors:
    - Query complexity
    - Training data availability
    - Model performance history
    - Cost constraints
    - Latency requirements
    """

    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.BALANCED):
        """
        Initialize model router.

        Args:
            strategy: Routing strategy to use
        """
        self.strategy = strategy

        # Model capabilities
        self.sagemaker_capabilities = {
            "yield_prediction": True,
            "harvest_date_prediction": True,
            "quality_prediction": True,
            "crop_recommendation": False,
            "annual_strategy": False,
            "market_analysis": False,
        }

        self.bedrock_capabilities = {
            "yield_prediction": True,
            "harvest_date_prediction": True,
            "quality_prediction": True,
            "crop_recommendation": True,
            "annual_strategy": True,
            "market_analysis": True,
        }

        # Performance thresholds
        self.min_training_samples = 100  # Minimum samples for SageMaker
        self.sagemaker_accuracy_threshold = 0.92  # 92% accuracy target
        self.bedrock_accuracy_threshold = 0.85  # 85% accuracy baseline

        # Cost thresholds (INR)
        self.max_cost_per_prediction = 3.0  # Target: < ₹3 per prediction
        self.sagemaker_cost = 0.17  # ~₹0.17 per inference
        self.bedrock_cost = 4.15  # ~₹4.15 per call

    def route_query(
        self,
        query_type: str,
        has_training_data: bool = True,
        training_samples: int = 0,
        is_batch: bool = False,
        latency_sensitive: bool = False,
        sagemaker_available: bool = True,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Route query to optimal model.

        Args:
            query_type: Type of query (yield_prediction, crop_recommendation, etc.)
            has_training_data: Whether training data exists
            training_samples: Number of training samples available
            is_batch: Whether this is a batch request
            latency_sensitive: Whether low latency is required
            sagemaker_available: Whether SageMaker endpoint is available

        Returns:
            Tuple of (model_type, routing_metadata)
        """
        routing_metadata = {
            "query_type": query_type,
            "strategy": self.strategy.value,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Check if query type is supported by SageMaker
        sagemaker_supports = self.sagemaker_capabilities.get(query_type, False)
        bedrock_supports = self.bedrock_capabilities.get(query_type, True)

        # If only Bedrock supports this query type, use Bedrock
        if not sagemaker_supports and bedrock_supports:
            routing_metadata["reason"] = "Only Bedrock supports this query type"
            routing_metadata["confidence"] = 1.0
            return "bedrock", routing_metadata

        # If SageMaker is unavailable, use Bedrock
        if not sagemaker_available:
            routing_metadata["reason"] = "SageMaker unavailable, using Bedrock fallback"
            routing_metadata["confidence"] = 1.0
            return "bedrock", routing_metadata

        # Check training data availability
        if sagemaker_supports and (
            not has_training_data or training_samples < self.min_training_samples
        ):
            routing_metadata["reason"] = (
                f"Insufficient training data ({training_samples} samples, need {self.min_training_samples})"
            )
            routing_metadata["confidence"] = 0.9
            return "bedrock", routing_metadata

        # Apply routing strategy
        if self.strategy == RoutingStrategy.ACCURACY_FIRST:
            return self._route_accuracy_first(
                query_type, is_batch, latency_sensitive, routing_metadata
            )

        elif self.strategy == RoutingStrategy.COST_FIRST:
            return self._route_cost_first(query_type, is_batch, latency_sensitive, routing_metadata)

        elif self.strategy == RoutingStrategy.BALANCED:
            return self._route_balanced(query_type, is_batch, latency_sensitive, routing_metadata)

        elif self.strategy == RoutingStrategy.FALLBACK_ONLY:
            return self._route_fallback_only(query_type, routing_metadata)

        # Default to Bedrock
        routing_metadata["reason"] = "Default routing to Bedrock"
        routing_metadata["confidence"] = 0.8
        return "bedrock", routing_metadata

    def _route_accuracy_first(
        self, query_type: str, is_batch: bool, latency_sensitive: bool, metadata: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Route with accuracy as primary concern.

        Prioritizes SageMaker for predictions (92-95% accuracy).
        """
        if self.sagemaker_capabilities.get(query_type, False):
            metadata["reason"] = "Accuracy-first: Using SageMaker for higher accuracy (92-95%)"
            metadata["expected_accuracy"] = "92-95%"
            metadata["confidence"] = 0.95
            return "sagemaker", metadata
        else:
            metadata["reason"] = "Accuracy-first: Using Bedrock (85-90% accuracy)"
            metadata["expected_accuracy"] = "85-90%"
            metadata["confidence"] = 0.85
            return "bedrock", metadata

    def _route_cost_first(
        self, query_type: str, is_batch: bool, latency_sensitive: bool, metadata: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Route with cost as primary concern.

        Uses SageMaker for batch (cost-effective), Bedrock for single queries.
        """
        if is_batch and self.sagemaker_capabilities.get(query_type, False):
            metadata["reason"] = "Cost-first: Using SageMaker for batch inference (₹0.17/call)"
            metadata["estimated_cost_inr"] = self.sagemaker_cost
            metadata["confidence"] = 0.9
            return "sagemaker", metadata
        else:
            # For single queries, Bedrock might be more cost-effective
            # considering cold start costs for SageMaker
            metadata["reason"] = "Cost-first: Using Bedrock for single query"
            metadata["estimated_cost_inr"] = self.bedrock_cost
            metadata["confidence"] = 0.85
            return "bedrock", metadata

    def _route_balanced(
        self, query_type: str, is_batch: bool, latency_sensitive: bool, metadata: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Route with balanced accuracy and cost.

        Uses SageMaker for complex predictions, Bedrock for reasoning.
        """
        # Complex predictions → SageMaker (better accuracy justifies cost)
        if query_type in ["yield_prediction", "harvest_date_prediction", "quality_prediction"]:
            if self.sagemaker_capabilities.get(query_type, False):
                metadata["reason"] = (
                    "Balanced: Using SageMaker for complex prediction (better accuracy)"
                )
                metadata["expected_accuracy"] = "92-95%"
                metadata["estimated_cost_inr"] = self.sagemaker_cost
                metadata["confidence"] = 0.92
                return "sagemaker", metadata

        # Reasoning and recommendations → Bedrock (sufficient accuracy, lower cost)
        metadata["reason"] = "Balanced: Using Bedrock for reasoning/recommendations"
        metadata["expected_accuracy"] = "85-90%"
        metadata["estimated_cost_inr"] = self.bedrock_cost
        metadata["confidence"] = 0.85
        return "bedrock", metadata

    def _route_fallback_only(
        self, query_type: str, metadata: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Route with Bedrock as primary, SageMaker as fallback.

        Conservative approach for testing.
        """
        metadata["reason"] = "Fallback-only: Using Bedrock as primary"
        metadata["expected_accuracy"] = "85-90%"
        metadata["estimated_cost_inr"] = self.bedrock_cost
        metadata["confidence"] = 0.85
        return "bedrock", metadata

    def evaluate_routing_decision(
        self,
        model_used: str,
        actual_accuracy: Optional[float] = None,
        actual_cost: Optional[float] = None,
        actual_latency_ms: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate routing decision based on actual results.

        Args:
            model_used: Model that was used
            actual_accuracy: Actual accuracy achieved
            actual_cost: Actual cost incurred (INR)
            actual_latency_ms: Actual latency in milliseconds

        Returns:
            Evaluation metrics
        """
        evaluation = {"model_used": model_used, "timestamp": datetime.now(UTC).isoformat()}

        # Evaluate accuracy
        if actual_accuracy is not None:
            expected_accuracy = (
                self.sagemaker_accuracy_threshold
                if model_used == "sagemaker"
                else self.bedrock_accuracy_threshold
            )

            evaluation["accuracy"] = {
                "actual": actual_accuracy,
                "expected": expected_accuracy,
                "meets_target": actual_accuracy >= expected_accuracy,
                "difference": actual_accuracy - expected_accuracy,
            }

        # Evaluate cost
        if actual_cost is not None:
            evaluation["cost"] = {
                "actual_inr": actual_cost,
                "target_inr": self.max_cost_per_prediction,
                "meets_target": actual_cost <= self.max_cost_per_prediction,
                "difference_inr": self.max_cost_per_prediction - actual_cost,
            }

        # Evaluate latency
        if actual_latency_ms is not None:
            target_latency = 500  # 500ms target for 95th percentile
            evaluation["latency"] = {
                "actual_ms": actual_latency_ms,
                "target_ms": target_latency,
                "meets_target": actual_latency_ms <= target_latency,
                "difference_ms": target_latency - actual_latency_ms,
            }

        return evaluation

    def get_routing_recommendation(
        self, query_type: str, historical_performance: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get routing recommendation based on historical performance.

        Args:
            query_type: Type of query
            historical_performance: Historical performance data

        Returns:
            Routing recommendation with reasoning
        """
        recommendation = {"query_type": query_type, "timestamp": datetime.now(UTC).isoformat()}

        # If no historical data, use default routing
        if not historical_performance:
            model, metadata = self.route_query(query_type)
            recommendation["recommended_model"] = model
            recommendation["reason"] = metadata.get("reason")
            recommendation["confidence"] = metadata.get("confidence", 0.8)
            return recommendation

        # Analyze historical performance
        sagemaker_perf = historical_performance.get("sagemaker", {})
        bedrock_perf = historical_performance.get("bedrock", {})

        sagemaker_accuracy = sagemaker_perf.get("accuracy", 0.92)
        bedrock_accuracy = bedrock_perf.get("accuracy", 0.85)

        sagemaker_cost = sagemaker_perf.get("avg_cost_inr", self.sagemaker_cost)
        bedrock_cost = bedrock_perf.get("avg_cost_inr", self.bedrock_cost)

        # Calculate value score (accuracy / cost)
        sagemaker_value = sagemaker_accuracy / sagemaker_cost if sagemaker_cost > 0 else 0
        bedrock_value = bedrock_accuracy / bedrock_cost if bedrock_cost > 0 else 0

        if sagemaker_value > bedrock_value:
            recommendation["recommended_model"] = "sagemaker"
            recommendation["reason"] = (
                f"Better value: {sagemaker_accuracy:.1%} accuracy at ₹{sagemaker_cost:.2f}"
            )
            recommendation["confidence"] = 0.9
        else:
            recommendation["recommended_model"] = "bedrock"
            recommendation["reason"] = (
                f"Better value: {bedrock_accuracy:.1%} accuracy at ₹{bedrock_cost:.2f}"
            )
            recommendation["confidence"] = 0.85

        recommendation["value_scores"] = {
            "sagemaker": round(sagemaker_value, 2),
            "bedrock": round(bedrock_value, 2),
        }

        return recommendation


# Default router instance
default_router = ModelRouter(strategy=RoutingStrategy.BALANCED)
