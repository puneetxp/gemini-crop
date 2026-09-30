"""
Input validation and sanitization utilities for security
Prevents SQL injection, XSS attacks, and validates all user inputs
"""

import html
import re
from typing import Any, Dict, List, Optional

import bleach
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator


class InputSanitizer:
    """Sanitize user inputs to prevent injection attacks"""

    # Patterns for detecting malicious input
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|DECLARE)\b)",
        r"(--|;|\/\*|\*\/|xp_|sp_)",
        r"(\bOR\b.*=.*|1=1|'=')",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    @classmethod
    def sanitize_string(cls, value: str, allow_html: bool = False) -> str:
        """
        Sanitize string input to prevent XSS and injection attacks

        Args:
            value: Input string to sanitize
            allow_html: If True, allows safe HTML tags (for rich text)

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return value

        # Remove null bytes
        value = value.replace("\x00", "")

        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: potential SQL injection detected",
                )

        # Handle HTML/XSS
        if allow_html:
            # Allow only safe HTML tags
            allowed_tags = ["p", "br", "strong", "em", "u", "a", "ul", "ol", "li"]
            allowed_attrs = {"a": ["href", "title"]}
            value = bleach.clean(value, tags=allowed_tags, attributes=allowed_attrs, strip=True)
        else:
            # Check for XSS patterns
            for pattern in cls.XSS_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input: potential XSS attack detected",
                    )

            # Escape HTML entities
            value = html.escape(value)

        # Trim whitespace
        value = value.strip()

        return value

    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any], allow_html: bool = False) -> Dict[str, Any]:
        """
        Recursively sanitize all string values in a dictionary

        Args:
            data: Dictionary to sanitize
            allow_html: If True, allows safe HTML tags

        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_string(value, allow_html)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value, allow_html)
            elif isinstance(value, list):
                sanitized[key] = [
                    (
                        cls.sanitize_string(item, allow_html)
                        if isinstance(item, str)
                        else cls.sanitize_dict(item, allow_html) if isinstance(item, dict) else item
                    )
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized


class PhoneNumberValidator:
    """Validate and sanitize phone numbers"""

    # Indian phone number pattern: +91 followed by 10 digits
    INDIAN_PHONE_PATTERN = r"^\+91[6-9]\d{9}$"

    @classmethod
    def validate(cls, phone: str) -> str:
        """
        Validate and format Indian phone number

        Args:
            phone: Phone number string

        Returns:
            Formatted phone number

        Raises:
            HTTPException: If phone number is invalid
        """
        # Remove spaces and hyphens
        phone = re.sub(r"[\s\-\(\)]", "", phone)

        # Add +91 prefix if missing
        if not phone.startswith("+"):
            if phone.startswith("91"):
                phone = "+" + phone
            elif phone.startswith("0"):
                phone = "+91" + phone[1:]
            else:
                phone = "+91" + phone

        # Validate format
        if not re.match(cls.INDIAN_PHONE_PATTERN, phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format. Expected: +91XXXXXXXXXX (10 digits starting with 6-9)",
            )

        return phone


class NumericRangeValidator:
    """Validate numeric inputs are within acceptable ranges"""

    @staticmethod
    def validate_area(area: float, min_area: float = 0.1, max_area: float = 10000.0) -> float:
        """
        Validate land area in acres

        Args:
            area: Area value
            min_area: Minimum allowed area (default 0.1 acres)
            max_area: Maximum allowed area (default 10,000 acres)

        Returns:
            Validated area

        Raises:
            HTTPException: If area is out of range
        """
        if not isinstance(area, (int, float)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Area must be a number"
            )

        if area < min_area or area > max_area:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Area must be between {min_area} and {max_area} acres",
            )

        return float(area)

    @staticmethod
    def validate_coordinates(
        lat: Optional[float], lng: Optional[float]
    ) -> tuple[Optional[float], Optional[float]]:
        """
        Validate GPS coordinates

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            Tuple of validated (lat, lng)

        Raises:
            HTTPException: If coordinates are invalid
        """
        if lat is None and lng is None:
            return None, None

        if lat is None or lng is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both latitude and longitude must be provided",
            )

        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Coordinates must be numbers"
            )

        if lat < -90 or lat > 90:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Latitude must be between -90 and 90",
            )

        if lng < -180 or lng > 180:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Longitude must be between -180 and 180",
            )

        return float(lat), float(lng)

    @staticmethod
    def validate_quantity(
        quantity: float, min_qty: float = 0.0, max_qty: float = 1000000.0
    ) -> float:
        """
        Validate quantity values (crop quantity, livestock count, etc.)

        Args:
            quantity: Quantity value
            min_qty: Minimum allowed quantity
            max_qty: Maximum allowed quantity

        Returns:
            Validated quantity

        Raises:
            HTTPException: If quantity is out of range
        """
        if not isinstance(quantity, (int, float)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be a number"
            )

        if quantity < min_qty or quantity > max_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quantity must be between {min_qty} and {max_qty}",
            )

        return float(quantity)

    @staticmethod
    def validate_price(
        price: float, min_price: float = 0.0, max_price: float = 10000000.0
    ) -> float:
        """
        Validate price values

        Args:
            price: Price value
            min_price: Minimum allowed price
            max_price: Maximum allowed price

        Returns:
            Validated price

        Raises:
            HTTPException: If price is out of range
        """
        if not isinstance(price, (int, float)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Price must be a number"
            )

        if price < min_price or price > max_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Price must be between {min_price} and {max_price}",
            )

        return float(price)


class EnumValidator:
    """Validate enum/choice fields"""

    SOIL_TYPES = ["clay", "sandy", "loamy", "silt", "peat", "black", "red", "mixed"]
    IRRIGATION_TYPES = ["rain-fed", "canal", "borewell", "drip", "sprinkler", "mixed"]
    USER_TYPES = ["farmer", "buyer", "admin"]
    CROP_SEASONS = ["kharif", "rabi", "zaid"]
    QUALITY_GRADES = ["A", "B", "C"]
    LISTING_STATUS = ["active", "reserved", "sold", "expired"]
    INTEREST_STATUS = ["pending", "contacted", "completed", "cancelled"]

    @classmethod
    def validate_choice(cls, value: str, allowed_values: List[str], field_name: str) -> str:
        """
        Validate that value is in allowed choices

        Args:
            value: Value to validate
            allowed_values: List of allowed values
            field_name: Name of the field (for error message)

        Returns:
            Validated value (lowercase)

        Raises:
            HTTPException: If value is not in allowed choices
        """
        if not isinstance(value, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"{field_name} must be a string"
            )

        value_lower = value.lower().strip()

        if value_lower not in [v.lower() for v in allowed_values]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} must be one of: {', '.join(allowed_values)}",
            )

        return value_lower


class RequestSizeValidator:
    """Validate request sizes to prevent DoS attacks"""

    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_JSON_FIELDS = 1000  # Maximum number of fields in JSON
    MAX_STRING_LENGTH = 10000  # Maximum string length
    MAX_ARRAY_LENGTH = 1000  # Maximum array length
    # Fields named *_base64 carry a file (voice recording, crop photo). A 2-second clip is
    # already over 10,000 characters, so these are bounded only by MAX_REQUEST_SIZE
    # (checked on the whole body) and by each endpoint's own decoded-size check.
    BINARY_FIELD_SUFFIX = "_base64"

    @classmethod
    def validate_json_size(cls, data: Dict[str, Any]) -> None:
        """
        Validate JSON request size and complexity

        Args:
            data: JSON data to validate

        Raises:
            HTTPException: If request is too large or complex
        """
        # Count total fields
        field_count = cls._count_fields(data)
        if field_count > cls.MAX_JSON_FIELDS:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request too complex: maximum {cls.MAX_JSON_FIELDS} fields allowed",
            )

        # Check string lengths and array sizes
        cls._validate_values(data)

    @classmethod
    def _count_fields(cls, data: Any, count: int = 0) -> int:
        """Recursively count fields in nested structure"""
        if isinstance(data, dict):
            count += len(data)
            for value in data.values():
                count = cls._count_fields(value, count)
        elif isinstance(data, list):
            for item in data:
                count = cls._count_fields(item, count)
        return count

    @classmethod
    def _validate_values(cls, data: Any, key: str = "") -> None:
        """Recursively validate string lengths and array sizes"""
        if isinstance(data, str) and key.endswith(cls.BINARY_FIELD_SUFFIX):
            return
        if isinstance(data, str):
            if len(data) > cls.MAX_STRING_LENGTH:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"String too long: maximum {cls.MAX_STRING_LENGTH} characters allowed",
                )
        elif isinstance(data, list):
            if len(data) > cls.MAX_ARRAY_LENGTH:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Array too large: maximum {cls.MAX_ARRAY_LENGTH} items allowed",
                )
            for item in data:
                cls._validate_values(item)
        elif isinstance(data, dict):
            for field, value in data.items():
                cls._validate_values(value, str(field))


# Convenience functions for common validations


def sanitize_input(value: str, allow_html: bool = False) -> str:
    """Sanitize string input"""
    return InputSanitizer.sanitize_string(value, allow_html)


def validate_phone(phone: str) -> str:
    """Validate phone number"""
    return PhoneNumberValidator.validate(phone)


def validate_area(area: float) -> float:
    """Validate land area"""
    return NumericRangeValidator.validate_area(area)


def validate_coordinates(
    lat: Optional[float], lng: Optional[float]
) -> tuple[Optional[float], Optional[float]]:
    """Validate GPS coordinates"""
    return NumericRangeValidator.validate_coordinates(lat, lng)


def validate_enum(value: str, allowed_values: List[str], field_name: str) -> str:
    """Validate enum/choice field"""
    return EnumValidator.validate_choice(value, allowed_values, field_name)


def validate_request_size(data: Dict[str, Any]) -> None:
    """Validate request size"""
    RequestSizeValidator.validate_json_size(data)
