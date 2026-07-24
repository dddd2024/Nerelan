"""Risk and routing enums shared by the architecture spine."""

from enum import StrEnum


class RiskTier(StrEnum):
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"


class WorkflowRoute(StrEnum):
    STANDARD_PATH = "STANDARD_PATH"
    TRUST_AUTHORIZATION_REQUIRED = "TRUST_AUTHORIZATION_REQUIRED"
    BLOCKED = "BLOCKED"


class AuthorizationStatus(StrEnum):
    AUTHORIZED = "AUTHORIZED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    BLOCKED = "BLOCKED"


class AcceptanceStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    BLOCKED = "BLOCKED"
