"""Shared machine-stable contract values used by harness implementations."""

from __future__ import annotations

from enum import Enum


class HarnessErrorCode(str, Enum):
    UNAVAILABLE = "UNAVAILABLE"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    STALE_RESUME = "STALE_RESUME"
    SHADOW_CONFLICT = "SHADOW_CONFLICT"
    INVALID_ENVELOPE = "INVALID_ENVELOPE"
