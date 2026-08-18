"""Exceptions raised by the STRATUMvisor SDK."""
from __future__ import annotations

from typing import Any, Mapping, Optional


class StratumError(Exception):
    """Base class for all SDK errors."""


class StratumConnectionError(StratumError):
    """The controller could not be reached."""


class StratumTimeoutError(StratumConnectionError):
    """A controller request timed out."""


class StratumTLSException(StratumConnectionError):
    """TLS negotiation or certificate verification failed."""


class StratumAPIError(StratumError):
    """The STRATUM API returned an error response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        method: Optional[str] = None,
        url: Optional[str] = None,
        details: Any = None,
        response: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.method = method
        self.url = url
        self.details = details
        self.response = response

    def __str__(self) -> str:
        prefix = []
        if self.status_code is not None:
            prefix.append(str(self.status_code))
        if self.code:
            prefix.append(self.code)
        if prefix:
            return f"{' '.join(prefix)}: {self.message}"
        return self.message


class StratumAuthenticationError(StratumAPIError):
    """Authentication failed or the authentication session expired."""


class StratumAuthorizationError(StratumAPIError):
    """The authenticated identity is not authorized for the operation."""


class StratumNotFoundError(StratumAPIError):
    """The requested STRATUM resource does not exist."""


class StratumConflictError(StratumAPIError):
    """The requested mutation conflicts with current STRATUM state."""


class StratumValidationError(StratumAPIError):
    """STRATUM rejected the request as invalid."""


def error_code_from_payload(payload: Any, message: str = "") -> Optional[str]:
    """Extract a stable-looking STRATUM error code without inventing one."""
    if isinstance(payload, Mapping):
        for key in ("error_code", "errorCode", "reason_code", "reasonCode"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        data = payload.get("data")
        if isinstance(data, Mapping):
            for key in ("code", "error_code", "errorCode"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    text = (message or "").strip()
    if ":" in text:
        candidate = text.split(":", 1)[0].strip()
        if candidate and candidate.replace("_", "").isalnum() and candidate.upper() == candidate:
            return candidate
    return None
