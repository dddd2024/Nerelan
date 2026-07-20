"""Trust authorization boundary for high-risk architecture work."""

from .authorization import TransitionKernelAuthorizationAdapter, TrustAuthorizationPort

__all__ = ["TransitionKernelAuthorizationAdapter", "TrustAuthorizationPort"]
