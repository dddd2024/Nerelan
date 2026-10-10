"""Explicit synthetic identities for existing authenticated positive clients."""
from reverse_agent.platform_v1.local_client_session import LocalClientSession

CLIENT_TOKEN = "a" * 64
CLIENT_HEADER = "X-Nerelan-Client-Capability"


def client_session(*, activate=True):
    sequence = iter((CLIENT_TOKEN, "b" * 64, "c" * 64, "d" * 64))
    session = LocalClientSession(token_factory=lambda: next(sequence))
    if activate:
        session.rotate()
    return session


def client_headers(headers=None):
    return {**(headers or {}), CLIENT_HEADER: CLIENT_TOKEN}
