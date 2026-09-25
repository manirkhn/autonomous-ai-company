"""
Cloud Environment & Public URL Configuration (Phase 5F).
Manages PUBLIC_BASE_URL, environment detection (DEVELOPMENT, STAGING, PRODUCTION),
and runtime deployment identity without hardcoding localhost.
"""

import os
import socket
import platform
from typing import Dict, Any, Optional
from datetime import datetime, timezone

class CloudConfig:
    """
    Central environment and URL configuration for public customer accessibility.
    """

    @classmethod
    def get_environment(cls) -> str:
        """
        Returns execution environment: DEVELOPMENT, STAGING, or PRODUCTION.
        """
        explicit = os.environ.get("ENVIRONMENT", "").upper()
        if explicit in ("DEVELOPMENT", "STAGING", "PRODUCTION"):
            return explicit
        
        # Check cloud provider signals
        if os.environ.get("RENDER") or os.environ.get("FLY_APP_NAME") or os.environ.get("KUBERNETES_SERVICE_HOST"):
            return "PRODUCTION"
        
        return "DEVELOPMENT"

    @classmethod
    def get_public_base_url(cls) -> Optional[str]:
        """
        Returns the configured public base URL (e.g. 'https://autonomous-ai-company.onrender.com').
        Returns None or empty string if not configured in production.
        In development, returns None unless explicitly set or requested with fallback.
        """
        url = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
        if url:
            return url
        
        # Check well-known cloud provider environment variables
        if os.environ.get("RENDER_EXTERNAL_URL"):
            return os.environ.get("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
        if os.environ.get("FLY_APP_NAME"):
            return f"https://{os.environ.get('FLY_APP_NAME')}.fly.dev"
        
        return None

    @classmethod
    def get_effective_base_url(cls) -> str:
        """
        Returns the base URL to use for requests.
        Falls back to local host if in development.
        """
        public_url = cls.get_public_base_url()
        if public_url:
            return public_url
        
        host = os.environ.get("HOST", "127.0.0.1")
        port = os.environ.get("PORT", "8000")
        return f"http://{host}:{port}"

    @classmethod
    def get_customer_product_url(cls) -> str:
        """
        Returns the public customer-facing URL for the product page.
        """
        base = cls.get_effective_base_url()
        return f"{base}/product"

    @classmethod
    def get_customer_checkout_url(cls, session_id_or_order_id: str = "") -> str:
        """
        Returns customer-facing checkout URL.
        """
        base = cls.get_effective_base_url()
        if session_id_or_order_id:
            return f"{base}/checkout/{session_id_or_order_id}"
        return f"{base}/api/payments/checkout"

    @classmethod
    def get_payment_mode(cls) -> str:
        """
        Returns PAYMENT_MODE: SANDBOX, PRODUCTION, or UNKNOWN.
        """
        explicit = os.environ.get("PAYMENT_MODE", "").upper()
        if explicit in ("SANDBOX", "PRODUCTION"):
            return explicit
        
        # Check if production Stripe live credentials are set
        stripe_key = os.environ.get("STRIPE_API_KEY", "")
        if stripe_key.startswith("sk_live_"):
            return "PRODUCTION"
        elif stripe_key.startswith("sk_test_"):
            return "SANDBOX"
        
        return "SANDBOX"

    @classmethod
    def get_runtime_type(cls) -> str:
        """
        Determines the current runtime type.
        """
        if os.environ.get("RENDER"):
            return "RENDER_CLOUD_CONTAINER"
        elif os.environ.get("FLY_APP_NAME"):
            return "FLY_IO_CLOUD_CONTAINER"
        elif os.environ.get("KUBERNETES_SERVICE_HOST"):
            return "KUBERNETES_POD"
        elif os.environ.get("DOCKER_CONTAINER") or os.path.exists("/.dockerenv"):
            return "DOCKER_CONTAINER"
        elif os.environ.get("REMOTE_CLOUD", "").lower() in ("true", "1", "yes"):
            return "REMOTE_CLOUD_VM"
        else:
            return "LOCAL_WORKSTATION"

    @classmethod
    def is_cloud_runtime(cls) -> bool:
        return cls.get_runtime_type() != "LOCAL_WORKSTATION"

    @classmethod
    def get_environment_info(cls) -> Dict[str, Any]:
        """
        Returns safe, comprehensive operational environment metadata.
        """
        public_url = cls.get_public_base_url()
        is_cloud = cls.is_cloud_runtime()
        env = cls.get_environment()
        
        return {
            "environment": env,
            "runtime_type": cls.get_runtime_type(),
            "is_cloud_runtime": is_cloud,
            "public_base_url": public_url or "NOT_CONFIGURED",
            "is_public_configured": bool(public_url),
            "effective_url": cls.get_effective_base_url(),
            "payment_mode": cls.get_payment_mode(),
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": platform.python_version()
        }
