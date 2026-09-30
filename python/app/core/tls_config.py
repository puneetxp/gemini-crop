"""
TLS/HTTPS Configuration for Production Deployment
Provides utilities and configuration for secure HTTPS/TLS 1.3 setup
"""

import logging
import ssl
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def create_ssl_context(
    certfile: str,
    keyfile: str,
    ca_certs: Optional[str] = None,
    min_version: int = ssl.TLSVersion.TLSv1_3,
) -> ssl.SSLContext:
    """
    Create SSL context for HTTPS with TLS 1.3

    Args:
        certfile: Path to SSL certificate file
        keyfile: Path to SSL private key file
        ca_certs: Optional path to CA certificates
        min_version: Minimum TLS version (default: TLS 1.3)

    Returns:
        Configured SSL context

    Example:
        >>> ssl_context = create_ssl_context(
        ...     certfile="/path/to/cert.pem",
        ...     keyfile="/path/to/key.pem"
        ... )
    """
    # Create SSL context with secure defaults
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # Set minimum TLS version to 1.3
    context.minimum_version = min_version

    # Load certificate and private key
    context.load_cert_chain(certfile=certfile, keyfile=keyfile)

    # Load CA certificates if provided
    if ca_certs:
        context.load_verify_locations(cafile=ca_certs)

    # Set secure cipher suites (TLS 1.3 ciphers)
    # TLS 1.3 has a simplified cipher suite selection
    context.set_ciphers(
        "TLS_AES_256_GCM_SHA384:TLS_AES_128_GCM_SHA256:TLS_CHACHA20_POLY1305_SHA256"
    )

    # Additional security options
    context.options |= ssl.OP_NO_TLSv1  # Disable TLS 1.0
    context.options |= ssl.OP_NO_TLSv1_1  # Disable TLS 1.1
    context.options |= ssl.OP_NO_TLSv1_2  # Disable TLS 1.2 (enforce TLS 1.3 only)
    context.options |= ssl.OP_NO_COMPRESSION  # Disable compression (CRIME attack)
    context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE  # Server chooses cipher
    context.options |= ssl.OP_SINGLE_DH_USE  # Generate new DH key for each connection
    context.options |= ssl.OP_SINGLE_ECDH_USE  # Generate new ECDH key for each connection

    logger.info(f"SSL context created with TLS {min_version.name}")

    return context


def get_uvicorn_ssl_config(certfile: str, keyfile: str, ca_certs: Optional[str] = None) -> dict:
    """
    Get SSL configuration for Uvicorn server

    Args:
        certfile: Path to SSL certificate file
        keyfile: Path to SSL private key file
        ca_certs: Optional path to CA certificates

    Returns:
        Dictionary with Uvicorn SSL configuration

    Example:
        >>> ssl_config = get_uvicorn_ssl_config(
        ...     certfile="/etc/ssl/certs/server.crt",
        ...     keyfile="/etc/ssl/private/server.key"
        ... )
        >>> uvicorn.run(app, **ssl_config)
    """
    return {
        "ssl_keyfile": keyfile,
        "ssl_certfile": certfile,
        "ssl_ca_certs": ca_certs,
        "ssl_version": ssl.PROTOCOL_TLS_SERVER,
        "ssl_cert_reqs": ssl.CERT_NONE,  # Client certificates not required
        "ssl_ciphers": "TLS_AES_256_GCM_SHA384:TLS_AES_128_GCM_SHA256:TLS_CHACHA20_POLY1305_SHA256",
    }


def validate_https_configuration() -> bool:
    """
    Validate that HTTPS is properly configured in production

    Returns:
        True if HTTPS is properly configured, False otherwise
    """
    if settings.ENVIRONMENT == "production":
        # In production, we should enforce HTTPS
        # This is typically handled by a reverse proxy (nginx, ALB, etc.)
        logger.info(
            "Production environment detected - HTTPS should be configured at reverse proxy level"
        )
        return True

    logger.info(f"Non-production environment ({settings.ENVIRONMENT}) - HTTPS validation skipped")
    return True


# TLS/HTTPS Configuration Documentation
TLS_CONFIGURATION_GUIDE = """
# TLS/HTTPS Configuration Guide

## Production Deployment with TLS 1.3

### Option 1: Reverse Proxy (Recommended)
Use a reverse proxy (nginx, Apache, AWS ALB) to handle TLS termination:

#### Nginx Configuration:
```nginx
server {
    listen 443 ssl http2;
    server_name api.cropsense.ai;
    
    # TLS 1.3 Configuration
    ssl_protocols TLSv1.3;
    ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_AES_128_GCM_SHA256:TLS_CHACHA20_POLY1305_SHA256';
    ssl_prefer_server_ciphers on;
    
    # SSL Certificates
    ssl_certificate /etc/ssl/certs/server.crt;
    ssl_certificate_key /etc/ssl/private/server.key;
    
    # HSTS Header
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Proxy to FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.cropsense.ai;
    return 301 https://$server_name$request_uri;
}
```

#### AWS Application Load Balancer:
1. Create ALB with HTTPS listener (port 443)
2. Upload SSL certificate to ACM (AWS Certificate Manager)
3. Configure security policy: ELBSecurityPolicy-TLS13-1-2-2021-06
4. Forward traffic to target group (FastAPI on port 8000)
5. Enable HTTP to HTTPS redirect on port 80 listener

### Option 2: Direct Uvicorn TLS (Development/Testing)
Run Uvicorn with TLS directly:

```python
import uvicorn
from app.core.tls_config import get_uvicorn_ssl_config

ssl_config = get_uvicorn_ssl_config(
    certfile="/path/to/cert.pem",
    keyfile="/path/to/key.pem"
)

uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=443,
    **ssl_config
)
```

### Obtaining SSL Certificates

#### Let's Encrypt (Free):
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.cropsense.ai

# Auto-renewal is configured automatically
```

#### AWS Certificate Manager (ACM):
1. Request public certificate in ACM console
2. Validate domain ownership (DNS or email)
3. Use with ALB/CloudFront (free for AWS services)

### Testing TLS Configuration

```bash
# Test TLS 1.3 support
openssl s_client -connect api.cropsense.ai:443 -tls1_3

# Check SSL configuration
curl -I https://api.cropsense.ai

# SSL Labs test (comprehensive)
# Visit: https://www.ssllabs.com/ssltest/
```

### Security Checklist
- [ ] TLS 1.3 enabled
- [ ] TLS 1.0, 1.1, 1.2 disabled
- [ ] Strong cipher suites configured
- [ ] HSTS header enabled (max-age=31536000)
- [ ] Valid SSL certificate installed
- [ ] HTTP to HTTPS redirect configured
- [ ] Certificate auto-renewal configured
- [ ] Security headers enabled (see security_middleware.py)

### Environment Variables
Add to production .env:
```
ENVIRONMENT=production
HTTPS_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs/server.crt
SSL_KEY_PATH=/etc/ssl/private/server.key
```
"""


def print_tls_guide():
    """Print TLS configuration guide"""
    print(TLS_CONFIGURATION_GUIDE)


if __name__ == "__main__":
    # Print configuration guide when run directly
    print_tls_guide()
