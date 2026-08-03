"""Security helpers for broker authentication flows."""

import hashlib
import hmac


def kite_checksum(api_key: str, request_token: str, api_secret: str) -> str:
    """Build the checksum required by Kite's session-token endpoint."""

    value = f"{api_key}{request_token}{api_secret}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def verify_kite_postback(payload: bytes, checksum: str, api_secret: str) -> bool:
    """Verify a Kite postback HMAC without leaking timing information."""

    expected = hmac.new(api_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, checksum)
