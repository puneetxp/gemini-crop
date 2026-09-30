"""
Password hashing utilities using bcrypt
Implements secure password hashing with configurable work factor
"""

import logging

from passlib.context import CryptContext

logger = logging.getLogger(__name__)

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    if not password:
        raise ValueError("Password cannot be empty")

    try:
        passwd_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(passwd_bytes, salt)
        return hashed.decode("utf-8")
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise ValueError("Failed to hash password")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    if not plain_password or not hashed_password:
        return False

    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be updated
    (e.g., if the work factor has been increased)

    Args:
        hashed_password: Hashed password to check

    Returns:
        True if password should be rehashed
    """
    try:
        return pwd_context.needs_update(hashed_password)
    except Exception:
        return False


def get_password_strength(password: str) -> dict:
    """
    Evaluate password strength

    Args:
        password: Password to evaluate

    Returns:
        Dictionary with strength metrics
    """
    if not password:
        return {"score": 0, "strength": "very_weak", "feedback": ["Password is required"]}

    score = 0
    feedback = []

    # Length check
    length = len(password)
    if length < 8:
        feedback.append("Password should be at least 8 characters")
    elif length >= 8:
        score += 1
    if length >= 12:
        score += 1
    if length >= 16:
        score += 1

    # Character variety checks
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    if has_lower:
        score += 1
    else:
        feedback.append("Add lowercase letters")

    if has_upper:
        score += 1
    else:
        feedback.append("Add uppercase letters")

    if has_digit:
        score += 1
    else:
        feedback.append("Add numbers")

    if has_special:
        score += 1
    else:
        feedback.append("Add special characters")

    # Common patterns check
    common_patterns = ["password", "123456", "qwerty", "admin", "letmein"]
    if any(pattern in password.lower() for pattern in common_patterns):
        score = max(0, score - 2)
        feedback.append("Avoid common patterns")

    # Determine strength level
    if score <= 2:
        strength = "very_weak"
    elif score <= 4:
        strength = "weak"
    elif score <= 6:
        strength = "medium"
    elif score <= 7:
        strength = "strong"
    else:
        strength = "very_strong"

    return {
        "score": score,
        "strength": strength,
        "feedback": feedback if feedback else ["Password is strong"],
    }
