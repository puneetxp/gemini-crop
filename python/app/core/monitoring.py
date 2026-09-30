"""
CloudWatch Monitoring Service for Application Performance Monitoring (APM)
Task 20.3: Set up application monitoring

This module provides:
- CloudWatch metrics publishing (API errors, response times, Bedrock costs)
- Custom metric tracking (user registrations, strategy generations, marketplace listings)
- Application performance monitoring with CloudWatch Insights
- Health check utilities

Validates: Requirements (Non-Functional - Reliability)
"""

import asyncio
import logging
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# boto3/CloudWatch is AWS-specific — import optionally so app runs on GCP without it
try:
    import boto3
    from botocore.exceptions import ClientError

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.info("boto3 not available — CloudWatch monitoring disabled (running on GCP)")


class CloudWatchMonitor:
    """
    CloudWatch monitoring service for application metrics and logs
    """

    def __init__(
        self,
        namespace: str = "RuralFarmingPlatform",
        region: str = "ap-south-1",
        enabled: bool = True,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ):
        """
        Initialize CloudWatch monitoring

        Args:
            namespace: CloudWatch namespace for metrics
            region: AWS region
            enabled: Enable/disable monitoring
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
        """
        self.namespace = namespace
        self.region = region
        self.enabled = enabled

        if self.enabled:
            if not BOTO3_AVAILABLE:
                logger.info("CloudWatch monitoring disabled — boto3 not installed")
                self.enabled = False
                return
            try:
                client_kwargs = {"region_name": region}
                if aws_access_key_id and aws_secret_access_key:
                    client_kwargs["aws_access_key_id"] = aws_access_key_id
                    client_kwargs["aws_secret_access_key"] = aws_secret_access_key

                self.cloudwatch = boto3.client("cloudwatch", **client_kwargs)
                self.logs = boto3.client("logs", **client_kwargs)
                logger.info(f"CloudWatch monitoring initialized (namespace: {namespace})")
            except Exception as e:
                logger.error(f"Failed to initialize CloudWatch clients: {e}")
                self.enabled = False

    # ==================== METRIC PUBLISHING ====================

    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "Count",
        dimensions: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Publish a single metric to CloudWatch

        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Metric unit (Count, Seconds, Milliseconds, Bytes, etc.)
            dimensions: Metric dimensions for filtering
            timestamp: Metric timestamp (default: now)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            metric_data = {
                "MetricName": metric_name,
                "Value": value,
                "Unit": unit,
                "Timestamp": timestamp or datetime.utcnow(),
            }

            if dimensions:
                metric_data["Dimensions"] = [{"Name": k, "Value": v} for k, v in dimensions.items()]

            self.cloudwatch.put_metric_data(Namespace=self.namespace, MetricData=[metric_data])
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "AccessDenied":
                logger.warning(
                    f"CloudWatch Access Denied for {metric_name}. Monitoring disabled for this session."
                )
                self.enabled = False
            else:
                logger.error(f"Failed to publish metric {metric_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing metric {metric_name}: {e}")
            return False

    def put_metrics_batch(self, metrics: List[Dict[str, Any]]) -> bool:
        """
        Publish multiple metrics in a single API call (more efficient)

        Args:
            metrics: List of metric dictionaries with keys:
                - metric_name: str
                - value: float
                - unit: str (optional, default: Count)
                - dimensions: Dict[str, str] (optional)
                - timestamp: datetime (optional)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not metrics:
            return False

        try:
            metric_data = []
            for metric in metrics:
                data = {
                    "MetricName": metric["metric_name"],
                    "Value": metric["value"],
                    "Unit": metric.get("unit", "Count"),
                    "Timestamp": metric.get("timestamp", datetime.utcnow()),
                }

                if "dimensions" in metric:
                    data["Dimensions"] = [
                        {"Name": k, "Value": v} for k, v in metric["dimensions"].items()
                    ]

                metric_data.append(data)

            # CloudWatch allows max 20 metrics per request
            for i in range(0, len(metric_data), 20):
                batch = metric_data[i : i + 20]
                self.cloudwatch.put_metric_data(Namespace=self.namespace, MetricData=batch)

            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "AccessDenied":
                logger.warning(
                    "CloudWatch Access Denied for metrics batch. Monitoring disabled for this session."
                )
                self.enabled = False
            else:
                logger.error(f"Failed to publish metrics batch: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing metrics batch: {e}")
            return False

    # ==================== API METRICS ====================

    def track_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[str] = None,
    ):
        """
        Track API request metrics

        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: Response status code
            response_time_ms: Response time in milliseconds
            user_id: User ID (optional)
        """
        dimensions = {"Endpoint": endpoint, "Method": method, "StatusCode": str(status_code)}

        metrics = [
            {"metric_name": "APIRequests", "value": 1, "unit": "Count", "dimensions": dimensions},
            {
                "metric_name": "APIResponseTime",
                "value": response_time_ms,
                "unit": "Milliseconds",
                "dimensions": dimensions,
            },
        ]

        # Track errors separately
        if status_code >= 400:
            metrics.append(
                {"metric_name": "APIErrors", "value": 1, "unit": "Count", "dimensions": dimensions}
            )

        self.put_metrics_batch(metrics)

    def track_api_error(self, endpoint: str, method: str, error_type: str, error_message: str):
        """
        Track API errors with detailed information

        Args:
            endpoint: API endpoint path
            method: HTTP method
            error_type: Type of error (ValidationError, DatabaseError, etc.)
            error_message: Error message
        """
        dimensions = {"Endpoint": endpoint, "Method": method, "ErrorType": error_type}

        self.put_metric(metric_name="APIErrors", value=1, unit="Count", dimensions=dimensions)

        # Log error details
        logger.error(
            f"API Error: {method} {endpoint} - {error_type}: {error_message}",
            extra={"dimensions": dimensions},
        )

    # ==================== BEDROCK METRICS ====================

    def track_bedrock_request(
        self,
        model_id: str,
        request_type: str,
        response_time_ms: float,
        input_tokens: int,
        output_tokens: int,
        estimated_cost_usd: float,
        success: bool = True,
    ):
        """
        Track Bedrock API usage and costs

        Args:
            model_id: Bedrock model ID
            request_type: Type of request (annual_strategy, yield_prediction, etc.)
            response_time_ms: Response time in milliseconds
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            estimated_cost_usd: Estimated cost in USD
            success: Whether request was successful
        """
        dimensions = {"ModelId": model_id, "RequestType": request_type, "Success": str(success)}

        metrics = [
            {
                "metric_name": "BedrockRequests",
                "value": 1,
                "unit": "Count",
                "dimensions": dimensions,
            },
            {
                "metric_name": "BedrockResponseTime",
                "value": response_time_ms,
                "unit": "Milliseconds",
                "dimensions": dimensions,
            },
            {
                "metric_name": "BedrockInputTokens",
                "value": input_tokens,
                "unit": "Count",
                "dimensions": dimensions,
            },
            {
                "metric_name": "BedrockOutputTokens",
                "value": output_tokens,
                "unit": "Count",
                "dimensions": dimensions,
            },
            {
                "metric_name": "BedrockCost",
                "value": estimated_cost_usd,
                "unit": "None",  # USD
                "dimensions": dimensions,
            },
        ]

        self.put_metrics_batch(metrics)

    # ==================== BUSINESS METRICS ====================

    def track_user_registration(self, user_type: str = "farmer"):
        """Track user registration"""
        self.put_metric(
            metric_name="UserRegistrations",
            value=1,
            unit="Count",
            dimensions={"UserType": user_type},
        )

    def track_strategy_generation(self, state: str, district: str, success: bool = True):
        """Track annual strategy generation"""
        self.put_metric(
            metric_name="StrategyGenerations",
            value=1,
            unit="Count",
            dimensions={"State": state, "District": district, "Success": str(success)},
        )

    def track_marketplace_listing(
        self, crop_type: str, state: str, action: str = "created"  # created, updated, sold
    ):
        """Track marketplace listing activity"""
        self.put_metric(
            metric_name="MarketplaceListings",
            value=1,
            unit="Count",
            dimensions={"CropType": crop_type, "State": state, "Action": action},
        )

    def track_buyer_interest(self, crop_type: str, state: str):
        """Track buyer interest in marketplace"""
        self.put_metric(
            metric_name="BuyerInterests",
            value=1,
            unit="Count",
            dimensions={"CropType": crop_type, "State": state},
        )

    # ==================== CACHE METRICS ====================

    def track_cache_operation(
        self, operation: str, cache_key_prefix: str  # hit, miss, set, delete
    ):
        """Track cache operations"""
        self.put_metric(
            metric_name="CacheOperations",
            value=1,
            unit="Count",
            dimensions={"Operation": operation, "KeyPrefix": cache_key_prefix},
        )

    # ==================== DATABASE METRICS ====================

    def track_database_query(
        self,
        query_type: str,  # select, insert, update, delete
        table_name: str,
        execution_time_ms: float,
        success: bool = True,
    ):
        """Track database query performance"""
        dimensions = {"QueryType": query_type, "TableName": table_name, "Success": str(success)}

        metrics = [
            {
                "metric_name": "DatabaseQueries",
                "value": 1,
                "unit": "Count",
                "dimensions": dimensions,
            },
            {
                "metric_name": "DatabaseQueryTime",
                "value": execution_time_ms,
                "unit": "Milliseconds",
                "dimensions": dimensions,
            },
        ]

        self.put_metrics_batch(metrics)

    # ==================== HEALTH CHECK UTILITIES ====================

    async def check_database_health(self) -> Dict[str, Any]:
        """
        Check database connectivity and performance

        Returns:
            Health status dictionary
        """
        try:
            from app.core.database import check_db_connection

            start_time = time.time()
            is_healthy = check_db_connection()
            response_time_ms = (time.time() - start_time) * 1000

            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "response_time_ms": round(response_time_ms, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def check_redis_health(self) -> Dict[str, Any]:
        """
        Check Redis connectivity and performance

        Returns:
            Health status dictionary
        """
        try:
            from app.core.cache import get_cache_manager

            cache_manager = get_cache_manager()

            if not cache_manager or not cache_manager.enabled:
                return {"status": "disabled", "timestamp": datetime.utcnow().isoformat()}

            start_time = time.time()
            # Test Redis with ping
            cache_manager.client.ping()
            response_time_ms = (time.time() - start_time) * 1000

            # Get Redis info
            info = cache_manager.client.info()

            return {
                "status": "healthy",
                "response_time_ms": round(response_time_ms, 2),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def check_bedrock_health(self) -> Dict[str, Any]:
        """Check Bedrock API connectivity"""
        if not BOTO3_AVAILABLE:
            return {
                "status": "disabled",
                "reason": "boto3 not available",
                "timestamp": datetime.utcnow().isoformat(),
            }
        try:
            bedrock = boto3.client("bedrock", region_name=self.region)
            start_time = time.time()

            # List available models as health check
            response = bedrock.list_foundation_models()
            response_time_ms = (time.time() - start_time) * 1000

            available_models = len(response.get("modelSummaries", []))

            return {
                "status": "healthy",
                "response_time_ms": round(response_time_ms, 2),
                "available_models": available_models,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Bedrock health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def get_comprehensive_health(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of all services

        Returns:
            Complete health status dictionary
        """
        # Run all health checks concurrently
        database_health, redis_health, bedrock_health = await asyncio.gather(
            self.check_database_health(),
            self.check_redis_health(),
            self.check_bedrock_health(),
            return_exceptions=True,
        )

        # Determine overall status
        all_healthy = all(
            [
                database_health.get("status") == "healthy",
                redis_health.get("status") in ["healthy", "disabled"],
                bedrock_health.get("status") == "healthy",
            ]
        )

        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": database_health,
                "redis": redis_health,
                "bedrock": bedrock_health,
            },
        }


# ==================== DECORATOR FOR AUTOMATIC MONITORING ====================


def monitor_endpoint(endpoint_name: Optional[str] = None):
    """
    Decorator to automatically monitor endpoint performance

    Usage:
        @monitor_endpoint("user_registration")
        async def register_user(...):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            monitor = get_monitor()
            start_time = time.time()
            error_occurred = False
            error_type = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error_occurred = True
                error_type = type(e).__name__
                raise
            finally:
                response_time_ms = (time.time() - start_time) * 1000

                # Track metrics
                if monitor and monitor.enabled:
                    name = endpoint_name or func.__name__
                    dimensions = {"Function": name, "Success": str(not error_occurred)}

                    if error_type:
                        dimensions["ErrorType"] = error_type

                    monitor.put_metrics_batch(
                        [
                            {
                                "metric_name": "FunctionInvocations",
                                "value": 1,
                                "unit": "Count",
                                "dimensions": dimensions,
                            },
                            {
                                "metric_name": "FunctionDuration",
                                "value": response_time_ms,
                                "unit": "Milliseconds",
                                "dimensions": dimensions,
                            },
                        ]
                    )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            monitor = get_monitor()
            start_time = time.time()
            error_occurred = False
            error_type = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error_occurred = True
                error_type = type(e).__name__
                raise
            finally:
                response_time_ms = (time.time() - start_time) * 1000

                # Track metrics
                if monitor and monitor.enabled:
                    name = endpoint_name or func.__name__
                    dimensions = {"Function": name, "Success": str(not error_occurred)}

                    if error_type:
                        dimensions["ErrorType"] = error_type

                    monitor.put_metrics_batch(
                        [
                            {
                                "metric_name": "FunctionInvocations",
                                "value": 1,
                                "unit": "Count",
                                "dimensions": dimensions,
                            },
                            {
                                "metric_name": "FunctionDuration",
                                "value": response_time_ms,
                                "unit": "Milliseconds",
                                "dimensions": dimensions,
                            },
                        ]
                    )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ==================== SINGLETON INSTANCE ====================

_monitor_instance: Optional[CloudWatchMonitor] = None


def init_monitor(
    namespace: str = "RuralFarmingPlatform",
    region: str = "ap-south-1",
    enabled: bool = True,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
) -> CloudWatchMonitor:
    """
    Initialize CloudWatch monitor singleton

    Args:
        namespace: CloudWatch namespace
        region: AWS region
        enabled: Enable/disable monitoring
        aws_access_key_id: AWS access key ID
        aws_secret_access_key: AWS secret access key

    Returns:
        CloudWatchMonitor instance
    """
    global _monitor_instance
    _monitor_instance = CloudWatchMonitor(
        namespace=namespace,
        region=region,
        enabled=enabled,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    return _monitor_instance


def get_monitor() -> Optional[CloudWatchMonitor]:
    """Get CloudWatch monitor singleton instance"""
    return _monitor_instance
