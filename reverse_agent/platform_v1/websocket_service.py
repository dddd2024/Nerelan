"""
WebSocket service for real-time communication between frontend and backend.
Provides live task updates, agent status, and streaming responses.
"""

import asyncio
import json
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler
from ipaddress import ip_address
from threading import Lock, Thread
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import unquote, urlsplit
from websocketserver import WebSocketServer

logger = logging.getLogger(__name__)

_DEFAULT_WS_HOST = "127.0.0.1"
_DEFAULT_WS_PORT = 8767


@dataclass
class WSClient:
    client_id: str
    address: tuple
    subscribed_topics: Set[str] = field(default_factory=set)
    connected_at: float = field(default_factory=time.time)


@dataclass
class WSServer:
    host: str = _DEFAULT_WS_HOST
    port: int = _DEFAULT_WS_PORT
    server: Any = None
    clients: Dict[str, WSClient] = field(default_factory=dict)
    lock: Lock = field(default_factory=Lock)
    _topic_subscribers: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))


class WebSocketService:
    """
    WebSocket service for real-time bidirectional communication.

    Topics:
    - task:{task_id} - Task-specific updates
    - agent:{agent_id} - Agent-specific status
    - system - System-wide announcements
    - log:{task_id} - Task execution logs
    """

    def __init__(
        self,
        host: str = _DEFAULT_WS_HOST,
        port: int = _DEFAULT_WS_PORT,
        allowed_origin: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.allowed_origin = allowed_origin or f"http://{host}:{port}"
        self._server = None
        self._clients: Dict[str, WSClient] = {}
        self._topic_subscribers: Dict[str, Set[str]] = defaultdict(set)
        self._lock = Lock()
        self._event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._running = False
        self._thread: Optional[Thread] = None

    def start(self):
        """Start the WebSocket server in a background thread."""
        if self._running:
            return

        self._running = True
        self._thread = Thread(target=self._run_server, daemon=True)
        self._thread.start()
        logger.info(f"WebSocket service started on ws://{self.host}:{self.port}")

    def stop(self):
        """Stop the WebSocket server."""
        self._running = False
        if self._server:
            self._server.shutdown()
        logger.info("WebSocket service stopped")

    def _run_server(self):
        """Run the WebSocket server."""
        try:
            from websocketserver import WebSocketServer
            self._server = WebSocketServer(
                self.host,
                self.port,
                self._on_connect,
                self._on_message,
                self._on_disconnect,
            )
            self._server.serve_forever()
        except ImportError:
            logger.warning(
                "websocketserver not installed. Using fallback polling mode. "
                "Install with: pip install websocketserver"
            )
            self._fallback_server()
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")
            self._fallback_server()

    def _fallback_server(self):
        """Fallback to a simple polling mechanism if WebSocket is not available."""
        while self._running:
            time.sleep(1)

    def _on_connect(self, client):
        """Handle new client connection."""
        client_id = f"client_{id(client)}_{int(time.time() * 1000)}"
        ws_client = WSClient(
            client_id=client_id,
            address=client.address if hasattr(client, "address") else ("unknown", 0),
        )
        with self._lock:
            self._clients[client_id] = ws_client

        self._send_to_client(client, {
            "type": "connected",
            "client_id": client_id,
            "server_time": time.time(),
        })
        logger.info(f"WebSocket client connected: {client_id}")

    def _on_message(self, client, message):
        """Handle incoming message from client."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "subscribe":
                topic = data.get("topic")
                if topic:
                    self._subscribe(client, topic)
            elif msg_type == "unsubscribe":
                topic = data.get("topic")
                if topic:
                    self._unsubscribe(client, topic)
            elif msg_type == "ping":
                self._send_to_client(client, {"type": "pong", "time": time.time()})
            elif msg_type == "get_status":
                self._handle_status_request(client, data)
            else:
                logger.debug(f"Unknown message type: {msg_type}")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON received from client")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def _on_disconnect(self, client):
        """Handle client disconnection."""
        client_id = None
        with self._lock:
            for cid, ws_client in self._clients.items():
                if ws_client.address == getattr(client, "address", None):
                    client_id = cid
                    break
            if client_id:
                del self._clients[client_id]
                # Clean up subscriptions
                for topic in list(self._topic_subscribers.keys()):
                    self._topic_subscribers[topic].discard(client_id)
                    if not self._topic_subscribers[topic]:
                        del self._topic_subscribers[topic]
        logger.info(f"WebSocket client disconnected: {client_id}")

    def _subscribe(self, client, topic: str):
        """Subscribe a client to a topic."""
        client_id = None
        with self._lock:
            for cid, ws_client in self._clients.items():
                if ws_client.address == getattr(client, "address", None):
                    client_id = cid
                    ws_client.subscribed_topics.add(topic)
                    self._topic_subscribers[topic].add(cid)
                    break

        self._send_to_client(client, {
            "type": "subscribed",
            "topic": topic,
            "client_id": client_id,
        })
        logger.debug(f"Client {client_id} subscribed to {topic}")

    def _unsubscribe(self, client, topic: str):
        """Unsubscribe a client from a topic."""
        client_id = None
        with self._lock:
            for cid, ws_client in self._clients.items():
                if ws_client.address == getattr(client, "address", None):
                    client_id = cid
                    ws_client.subscribed_topics.discard(topic)
                    self._topic_subscribers[topic].discard(cid)
                    break

        self._send_to_client(client, {
            "type": "unsubscribed",
            "topic": topic,
            "client_id": client_id,
        })

    def _handle_status_request(self, client, data: dict):
        """Handle status request from client."""
        status = {
            "type": "status_response",
            "request_id": data.get("request_id"),
            "clients_connected": len(self._clients),
            "topics_active": list(self._topic_subscribers.keys()),
            "server_time": time.time(),
        }
        self._send_to_client(client, status)

    def broadcast(self, topic: str, data: dict):
        """Broadcast a message to all clients subscribed to a topic."""
        message = json.dumps({"type": "broadcast", "topic": topic, "data": data})
        with self._lock:
            subscriber_ids = self._topic_subscribers.get(topic, set())
            for client_id in subscriber_ids:
                client = self._clients.get(client_id)
                if client:
                    self._send_to_client_by_id(client_id, message)

    def broadcast_all(self, data: dict):
        """Broadcast a message to all connected clients."""
        message = json.dumps({"type": "broadcast", "topic": "system", "data": data})
        with self._lock:
            for client_id in self._clients:
                self._send_to_client_by_id(client_id, message)

    def send_task_update(self, task_id: str, update: dict):
        """Send a task-specific update."""
        self.broadcast(f"task:{task_id}", {
            "event": "task_update",
            "task_id": task_id,
            **update,
        })

    def send_agent_status(self, agent_id: str, status: dict):
        """Send an agent status update."""
        self.broadcast(f"agent:{agent_id}", {
            "event": "agent_status",
            "agent_id": agent_id,
            **status,
        })

    def send_log_entry(self, task_id: str, log_entry: dict):
        """Send a log entry for a task."""
        self.broadcast(f"log:{task_id}", {
            "event": "log_entry",
            "task_id": task_id,
            **log_entry,
        })

    def send_system_announcement(self, announcement: dict):
        """Send a system-wide announcement."""
        self.broadcast("system", {
            "event": "system_announcement",
            **announcement,
        })

    def _send_to_client(self, client, data: dict):
        """Send data to a specific client."""
        try:
            if hasattr(client, "send"):
                client.send(json.dumps(data))
        except Exception as e:
            logger.error(f"Error sending to client: {e}")

    def _send_to_client_by_id(self, client_id: str, message: str):
        """Send a raw message to a client by ID."""
        with self._lock:
            client = self._clients.get(client_id)
            if client and hasattr(client, "_ws_client"):
                try:
                    client._ws_client.send(message)
                except Exception as e:
                    logger.error(f"Error sending to client {client_id}: {e}")

    def get_stats(self) -> dict:
        """Get server statistics."""
        with self._lock:
            return {
                "host": self.host,
                "port": self.port,
                "running": self._running,
                "clients_connected": len(self._clients),
                "topics_active": len(self._topic_subscribers),
                "subscriptions": {
                    topic: len(subscribers)
                    for topic, subscribers in self._topic_subscribers.items()
                },
            }


def create_websocket_service(
    host: str = _DEFAULT_WS_HOST,
    port: int = _DEFAULT_WS_PORT,
) -> WebSocketService:
    """Factory function to create a WebSocket service."""
    return WebSocketService(host=host, port=port)
