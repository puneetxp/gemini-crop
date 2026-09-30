"""
CloudWatch Alerting Service with SNS Notifications
Task 20.4: Configure alerting

This module provides:
- CloudWatch alarm creation and management
- SNS topic setup for notifications
- Alert configuration for API errors, performance, costs, and uptime
- Email and SMS notification support

Validates: Requirements (Non-Functional - Reliability)
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class AlarmSeverity(str, Enum):
    """Alarm severity levels"""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AlertingService:
    """
    CloudWatch alerting service with SNS notifications
    """

    def __init__(
        self,
        region: str = "ap-south-1",
        namespace: str = "RuralFarmingPlatform",
        enabled: bool = True,
    ):
        """
        Initialize alerting service

        Args:
            region: AWS region
            namespace: CloudWatch namespace
            enabled: Enable/disable alerting
        """
        self.region = region
        self.namespace = namespace
        self.enabled = enabled

        if self.enabled:
            try:
                self.cloudwatch = boto3.client("cloudwatch", region_name=region)
                self.sns = boto3.client("sns", region_name=region)
                logger.info(f"Alerting service initialized (region: {region})")
            except Exception as e:
                logger.error(f"Failed to initialize alerting clients: {e}")
                self.enabled = False

    # ==================== SNS TOPIC MANAGEMENT ====================

    def create_sns_topic(self, topic_name: str, display_name: str) -> Optional[str]:
        """
        Create SNS topic for notifications

        Args:
            topic_name: Topic name
            display_name: Display name for notifications

        Returns:
            Topic ARN if successful, None otherwise
        """
        if not self.enabled:
            return None

        try:
            response = self.sns.create_topic(
                Name=topic_name, Attributes={"DisplayName": display_name}
            )
            topic_arn = response["TopicArn"]
            logger.info(f"SNS topic created: {topic_name} ({topic_arn})")
            return topic_arn

        except ClientError as e:
            if e.response["Error"]["Code"] == "TopicAlreadyExists":
                # Get existing topic ARN
                response = self.sns.create_topic(Name=topic_name)
                topic_arn = response["TopicArn"]
                logger.info(f"Using existing SNS topic: {topic_name} ({topic_arn})")
                return topic_arn
            else:
                logger.error(f"Failed to create SNS topic {topic_name}: {e}")
                return None

    def subscribe_email(self, topic_arn: str, email: str) -> bool:
        """
        Subscribe email to SNS topic

        Args:
            topic_arn: SNS topic ARN
            email: Email address

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            self.sns.subscribe(TopicArn=topic_arn, Protocol="email", Endpoint=email)
            logger.info(f"Email subscription created: {email} -> {topic_arn}")
            logger.info(f"Confirmation email sent to {email}")
            return True

        except ClientError as e:
            logger.error(f"Failed to subscribe email {email}: {e}")
            return False

    def subscribe_sms(self, topic_arn: str, phone_number: str) -> bool:
        """
        Subscribe phone number to SNS topic for SMS alerts

        Args:
            topic_arn: SNS topic ARN
            phone_number: Phone number (E.164 format: +919876543210)

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            self.sns.subscribe(TopicArn=topic_arn, Protocol="sms", Endpoint=phone_number)
            logger.info(f"SMS subscription created: {phone_number} -> {topic_arn}")
            return True

        except ClientError as e:
            logger.error(f"Failed to subscribe SMS {phone_number}: {e}")
            return False

    # ==================== ALARM CREATION ====================

    def create_alarm(
        self,
        alarm_name: str,
        alarm_description: str,
        metric_name: str,
        comparison_operator: str,
        threshold: float,
        evaluation_periods: int,
        period: int,
        statistic: str,
        sns_topic_arn: str,
        dimensions: Optional[List[Dict[str, str]]] = None,
        treat_missing_data: str = "notBreaching",
    ) -> bool:
        """
        Create CloudWatch alarm

        Args:
            alarm_name: Alarm name
            alarm_description: Alarm description
            metric_name: CloudWatch metric name
            comparison_operator: GreaterThanThreshold, LessThanThreshold, etc.
            threshold: Alarm threshold value
            evaluation_periods: Number of periods to evaluate
            period: Period in seconds
            statistic: Average, Sum, Maximum, Minimum, SampleCount
            sns_topic_arn: SNS topic ARN for notifications
            dimensions: Metric dimensions
            treat_missing_data: notBreaching, breaching, ignore, missing

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            alarm_config = {
                "AlarmName": alarm_name,
                "AlarmDescription": alarm_description,
                "ActionsEnabled": True,
                "AlarmActions": [sns_topic_arn],
                "MetricName": metric_name,
                "Namespace": self.namespace,
                "Statistic": statistic,
                "Period": period,
                "EvaluationPeriods": evaluation_periods,
                "Threshold": threshold,
                "ComparisonOperator": comparison_operator,
                "TreatMissingData": treat_missing_data,
            }

            if dimensions:
                alarm_config["Dimensions"] = dimensions

            self.cloudwatch.put_metric_alarm(**alarm_config)
            logger.info(f"Alarm created: {alarm_name}")
            return True

        except ClientError as e:
            logger.error(f"Failed to create alarm {alarm_name}: {e}")
            return False

    # ==================== API ERROR ALERTS ====================

    def create_api_error_rate_alarm(
        self, sns_topic_arn: str, threshold_percent: float = 5.0
    ) -> bool:
        """
        Create alarm for API error rate > threshold

        Args:
            sns_topic_arn: SNS topic ARN
            threshold_percent: Error rate threshold (default: 5%)

        Returns:
            True if successful
        """
        # Use metric math to calculate error rate percentage
        alarm_name = f"{self.namespace}-API-Error-Rate-High"

        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                AlarmDescription=f"API error rate exceeds {threshold_percent}%",
                ActionsEnabled=True,
                AlarmActions=[sns_topic_arn],
                EvaluationPeriods=2,
                DatapointsToAlarm=2,
                Threshold=threshold_percent,
                ComparisonOperator="GreaterThanThreshold",
                TreatMissingData="notBreaching",
                Metrics=[
                    {
                        "Id": "errors",
                        "MetricStat": {
                            "Metric": {"Namespace": self.namespace, "MetricName": "APIErrors"},
                            "Period": 300,
                            "Stat": "Sum",
                        },
                        "ReturnData": False,
                    },
                    {
                        "Id": "requests",
                        "MetricStat": {
                            "Metric": {"Namespace": self.namespace, "MetricName": "APIRequests"},
                            "Period": 300,
                            "Stat": "Sum",
                        },
                        "ReturnData": False,
                    },
                    {
                        "Id": "error_rate",
                        "Expression": "(errors / requests) * 100",
                        "Label": "Error Rate %",
                        "ReturnData": True,
                    },
                ],
            )
            logger.info(f"API error rate alarm created: {alarm_name}")
            return True

        except ClientError as e:
            logger.error(f"Failed to create API error rate alarm: {e}")
            return False

    def create_api_error_count_alarm(self, sns_topic_arn: str, threshold: int = 10) -> bool:
        """
        Create alarm for absolute API error count

        Args:
            sns_topic_arn: SNS topic ARN
            threshold: Error count threshold (default: 10 errors in 5 minutes)

        Returns:
            True if successful
        """
        return self.create_alarm(
            alarm_name=f"{self.namespace}-API-Error-Count-High",
            alarm_description=f"API errors exceed {threshold} in 5 minutes",
            metric_name="APIErrors",
            comparison_operator="GreaterThanThreshold",
            threshold=threshold,
            evaluation_periods=1,
            period=300,
            statistic="Sum",
            sns_topic_arn=sns_topic_arn,
        )

    # ==================== PERFORMANCE ALERTS ====================

    def create_api_response_time_alarm(
        self, sns_topic_arn: str, threshold_ms: float = 3000.0
    ) -> bool:
        """
        Create alarm for API response time > threshold

        Args:
            sns_topic_arn: SNS topic ARN
            threshold_ms: Response time threshold in milliseconds (default: 3000ms)

        Returns:
            True if successful
        """
        return self.create_alarm(
            alarm_name=f"{self.namespace}-API-Response-Time-High",
            alarm_description=f"API p95 response time exceeds {threshold_ms}ms",
            metric_name="APIResponseTime",
            comparison_operator="GreaterThanThreshold",
            threshold=threshold_ms,
            evaluation_periods=2,
            period=300,
            statistic="p95",
            sns_topic_arn=sns_topic_arn,
        )

    def create_bedrock_response_time_alarm(
        self, sns_topic_arn: str, threshold_ms: float = 10000.0
    ) -> bool:
        """
        Create alarm for Bedrock response time > threshold

        Args:
            sns_topic_arn: SNS topic ARN
            threshold_ms: Response time threshold in milliseconds (default: 10000ms)

        Returns:
            True if successful
        """
        return self.create_alarm(
            alarm_name=f"{self.namespace}-Bedrock-Response-Time-High",
            alarm_description=f"Bedrock p95 response time exceeds {threshold_ms}ms",
            metric_name="BedrockResponseTime",
            comparison_operator="GreaterThanThreshold",
            threshold=threshold_ms,
            evaluation_periods=2,
            period=300,
            statistic="p95",
            sns_topic_arn=sns_topic_arn,
        )

    # ==================== COST MONITORING ALERTS ====================

    def create_bedrock_cost_alarm(
        self, sns_topic_arn: str, daily_threshold_usd: float = 100.0
    ) -> bool:
        """
        Create alarm for Bedrock daily costs > threshold

        Args:
            sns_topic_arn: SNS topic ARN
            daily_threshold_usd: Daily cost threshold in USD (default: $100)

        Returns:
            True if successful
        """
        return self.create_alarm(
            alarm_name=f"{self.namespace}-Bedrock-Daily-Cost-High",
            alarm_description=f"Bedrock daily costs exceed ${daily_threshold_usd}",
            metric_name="BedrockCost",
            comparison_operator="GreaterThanThreshold",
            threshold=daily_threshold_usd,
            evaluation_periods=1,
            period=86400,  # 24 hours
            statistic="Sum",
            sns_topic_arn=sns_topic_arn,
        )

    def create_bedrock_hourly_cost_alarm(
        self, sns_topic_arn: str, hourly_threshold_usd: float = 10.0
    ) -> bool:
        """
        Create alarm for Bedrock hourly costs > threshold

        Args:
            sns_topic_arn: SNS topic ARN
            hourly_threshold_usd: Hourly cost threshold in USD (default: $10)

        Returns:
            True if successful
        """
        return self.create_alarm(
            alarm_name=f"{self.namespace}-Bedrock-Hourly-Cost-High",
            alarm_description=f"Bedrock hourly costs exceed ${hourly_threshold_usd}",
            metric_name="BedrockCost",
            comparison_operator="GreaterThanThreshold",
            threshold=hourly_threshold_usd,
            evaluation_periods=1,
            period=3600,  # 1 hour
            statistic="Sum",
            sns_topic_arn=sns_topic_arn,
        )

    # ==================== DATABASE ALERTS ====================

    def create_database_query_time_alarm(
        self, sns_topic_arn: str, threshold_ms: float = 500.0
    ) -> bool:
        """
        Create alarm for database query time > threshold

        Args:
            sns_topic_arn: SNS topic ARN
            threshold_ms: Query time threshold in milliseconds (default: 500ms)

        Returns:
            True if successful
        """
        return self.create_alarm(
            alarm_name=f"{self.namespace}-Database-Query-Time-High",
            alarm_description=f"Database p95 query time exceeds {threshold_ms}ms",
            metric_name="DatabaseQueryTime",
            comparison_operator="GreaterThanThreshold",
            threshold=threshold_ms,
            evaluation_periods=2,
            period=300,
            statistic="p95",
            sns_topic_arn=sns_topic_arn,
        )

    # ==================== UPTIME MONITORING ====================

    def create_health_check_alarm(self, sns_topic_arn: str, health_check_url: str) -> bool:
        """
        Create alarm for health check failures

        Note: This requires setting up a CloudWatch Synthetics Canary
        or using Route 53 health checks. This is a placeholder for
        the alarm configuration.

        Args:
            sns_topic_arn: SNS topic ARN
            health_check_url: Health check endpoint URL

        Returns:
            True if successful
        """
        logger.info(f"Health check alarm configuration for: {health_check_url}")
        logger.info("Note: Requires CloudWatch Synthetics Canary or Route 53 health check")

        # This would be configured with actual health check metrics
        # For now, we'll create an alarm based on API errors as a proxy
        return self.create_alarm(
            alarm_name=f"{self.namespace}-Service-Unhealthy",
            alarm_description="Service health check failing",
            metric_name="APIErrors",
            comparison_operator="GreaterThanThreshold",
            threshold=50,  # 50 errors in 5 minutes indicates service issues
            evaluation_periods=2,
            period=300,
            statistic="Sum",
            sns_topic_arn=sns_topic_arn,
        )

    # ==================== COMPOSITE ALARM SETUP ====================

    def setup_all_alarms(
        self, critical_topic_arn: str, warning_topic_arn: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Set up all recommended alarms

        Args:
            critical_topic_arn: SNS topic ARN for critical alerts
            warning_topic_arn: SNS topic ARN for warning alerts (optional)

        Returns:
            Dictionary with alarm names and creation status
        """
        if not warning_topic_arn:
            warning_topic_arn = critical_topic_arn

        results = {}

        # Critical alarms
        logger.info("Creating critical alarms...")
        results["api_error_rate"] = self.create_api_error_rate_alarm(
            critical_topic_arn, threshold_percent=5.0
        )
        results["api_error_count"] = self.create_api_error_count_alarm(
            critical_topic_arn, threshold=10
        )
        results["service_health"] = self.create_health_check_alarm(
            critical_topic_arn, health_check_url="/health"
        )

        # Performance alarms
        logger.info("Creating performance alarms...")
        results["api_response_time"] = self.create_api_response_time_alarm(
            warning_topic_arn, threshold_ms=3000.0
        )
        results["bedrock_response_time"] = self.create_bedrock_response_time_alarm(
            warning_topic_arn, threshold_ms=10000.0
        )
        results["database_query_time"] = self.create_database_query_time_alarm(
            warning_topic_arn, threshold_ms=500.0
        )

        # Cost alarms
        logger.info("Creating cost monitoring alarms...")
        results["bedrock_daily_cost"] = self.create_bedrock_cost_alarm(
            warning_topic_arn, daily_threshold_usd=100.0
        )
        results["bedrock_hourly_cost"] = self.create_bedrock_hourly_cost_alarm(
            critical_topic_arn, hourly_threshold_usd=10.0
        )

        # Summary
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        logger.info(f"Alarm setup complete: {success_count}/{total_count} successful")

        return results

    # ==================== ALARM MANAGEMENT ====================

    def list_alarms(self) -> List[Dict[str, Any]]:
        """
        List all alarms for this namespace

        Returns:
            List of alarm configurations
        """
        if not self.enabled:
            return []

        try:
            response = self.cloudwatch.describe_alarms(AlarmNamePrefix=self.namespace)
            return response.get("MetricAlarms", [])

        except ClientError as e:
            logger.error(f"Failed to list alarms: {e}")
            return []

    def delete_alarm(self, alarm_name: str) -> bool:
        """
        Delete an alarm

        Args:
            alarm_name: Alarm name

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            self.cloudwatch.delete_alarms(AlarmNames=[alarm_name])
            logger.info(f"Alarm deleted: {alarm_name}")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete alarm {alarm_name}: {e}")
            return False

    def get_alarm_state(self, alarm_name: str) -> Optional[str]:
        """
        Get current alarm state

        Args:
            alarm_name: Alarm name

        Returns:
            Alarm state (OK, ALARM, INSUFFICIENT_DATA) or None
        """
        if not self.enabled:
            return None

        try:
            response = self.cloudwatch.describe_alarms(AlarmNames=[alarm_name])
            alarms = response.get("MetricAlarms", [])
            if alarms:
                return alarms[0]["StateValue"]
            return None

        except ClientError as e:
            logger.error(f"Failed to get alarm state for {alarm_name}: {e}")
            return None


# ==================== SINGLETON INSTANCE ====================

_alerting_instance: Optional[AlertingService] = None


def init_alerting(
    region: str = "ap-south-1", namespace: str = "RuralFarmingPlatform", enabled: bool = True
) -> AlertingService:
    """
    Initialize alerting service singleton

    Args:
        region: AWS region
        namespace: CloudWatch namespace
        enabled: Enable/disable alerting

    Returns:
        AlertingService instance
    """
    global _alerting_instance
    _alerting_instance = AlertingService(region=region, namespace=namespace, enabled=enabled)
    return _alerting_instance


def get_alerting() -> Optional[AlertingService]:
    """Get alerting service singleton instance"""
    return _alerting_instance
