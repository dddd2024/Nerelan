"""
Server-Sent Events (SSE) service for streaming responses from agents.
Provides real-time streaming of agent thoughts, progress, and results.
"""

import json
import logging
import os
import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler
from ipaddress import ip_address
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import unquote, urlsplit

logger = logging.getLogger(__name__)

_DEFAULT_SSE_HOST = "127.0.0.1"
_DEFAULT_SSE_PORT = 8768


@dataclass
class SSEClient:
    client_id: str
    address: tuple
    task_id: Optional[str] = None
    connected_at: float = field(default_factory=time.time)
    last_event_id: int = 0


class SSEService:
    """
    Server-Sent Events service for streaming agent responses.

    Endpoints:
    - GET /events/{task_id} - Stream events for a specific task
    - GET /events/system - Stream system-wide events
    - POST /publish - Publish an event (internal use)
    """

    def __init__(
        self,
        host: str = _DEFAULT_SSE_HOST,
        port: int = _DEFAULT_SSE_PORT,
        allowed_origin: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.allowed_origin = allowed_origin or f"http://{host}:{port}"
        self._clients: Dict[str, SSEClient] = {}
        self._task_clients: Dict[str, List[str]] = defaultdict(list)
        self._system_clients: List[str] = []
        self._event_queue: Dict[str, List[dict]] = defaultdict(list)
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._event_counter = 0

    def start(self):
        """Start the SSE server in a background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        logger.info(f"SSE service started on http://{self.host}:{self.port}")

    def stop(self):
        """Stop the SSE server."""
        self._running = False
        logger.info("SSE service stopped")

    def _run_server(self):
        """Run the SSE server."""
        try:
            from http.server import HTTPServer
            server = HTTPServer(
                (self.host, self.port),
                SSERequestHandler,
            )
            server.sse_service = self
            server.serve_forever()
        except Exception as e:
            logger.error(f"SSE server error: {e}")

    def publish_event(self, task_id: str, event_type: str, data: dict, event_id: Optional[int] = None):
        """Publish an event to all clients subscribed to a task."""
        if event_id is None:
            self._event_counter += 1
            event_id = self._event_counter

        event = {
            "id": event_id,
            "event": event_type,
            "data": json.dumps(data),
            "timestamp": time.time(),
        }

        with self._lock:
            self._event_queue[task_id].append(event)
            # Keep only last 100 events per task
            if len(self._event_queue[task_id]) > 100:
                self._event_queue[task_id] = self._event_queue[task_id][-100:]

        # Notify connected clients
        self._notify_task_clients(task_id, event)

    def publish_system_event(self, event_type: str, data: dict, event_id: Optional[int] = None):
        """Publish a system-wide event."""
        if event_id is None:
            self._event_counter += 1
            event_id = self._event_counter

        event = {
            "id": event_id,
            "event": event_type,
            "data": json.dumps(data),
            "timestamp": time.time(),
        }

        self._notify_system_clients(event)

    def _notify_task_clients(self, task_id: str, event: dict):
        """Notify all clients subscribed to a task."""
        with self._lock:
            client_ids = self._task_clients.get(task_id, [])
            for client_id in client_ids:
                client = self._clients.get(client_id)
                if client:
                    try:
                        self._send_event(client, event)
                    except Exception:
                        # Client disconnected
                        self._remove_client(client_id)

    def _notify_system_clients(self, event: dict):
        """Notify all system event clients."""
        with self._lock:
            client_ids = self._system_clients.copy()
            for client_id in client_ids:
                client = self._clients.get(client_id)
                if client:
                    try:
                        self._send_event(client, event)
                    except Exception:
                        self._remove_client(client_id)

    def _send_event(self, client: SSEClient, event: dict):
        """Send an SSE event to a client."""
        # This is handled by the HTTP handler
        pass

    def add_task_client(self, client_id: str, task_id: str):
        """Add a client to a task's subscription list."""
        with self._lock:
            self._task_clients[task_id].append(client_id)

    def add_system_client(self, client_id: str):
        """Add a client to the system subscription list."""
        with self._lock:
            self._system_clients.append(client_id)

    def remove_client(self, client_id: str):
        """Remove a client from all subscriptions."""
        self._remove_client(client_id)

    def _remove_client(self, client_id: str):
        """Internal method to remove a client."""
        with self._lock:
            if client_id in self._clients:
                del self._clients[client_id]
            
            # Remove from task subscriptions
            for task_id in list(self._task_clients.keys()):
                if client_id in self._task_clients[task_id]:
                    self._task_clients[task_id].remove(client_id)
            
            # Remove from system subscriptions
            if client_id in self._system_clients:
                self._system_clients.remove(client_id)

    def get_client(self, client_id: str) -> Optional[SSEClient]:
        """Get a client by ID."""
        with self._lock:
            return self._clients.get(client_id)

    def register_client(self, client_id: str, address: tuple) -> SSEClient:
        """Register a new client."""
        client = SSEClient(client_id=client_id, address=address)
        with self._lock:
            self._clients[client_id] = client
        return client

    def get_stats(self) -> dict:
        """Get service statistics."""
        with self._lock:
            return {
                "host": self.host,
                "port": self.port,
                "running": self._running,
                "clients_connected": len(self._clients),
                "task_subscriptions": len(self._task_clients),
                "system_subscribers": len(self._system_clients),
            }


class SSERequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for SSE endpoints."""

    def do_GET(self):
        """Handle GET requests for SSE streams."""
        path = urlsplit(self.path).path
        
        # CORS headers
        self.send_header("Access-Control-Allow-Origin", self.server.sse_service.allowed_origin)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Cache-Control, Last-Event-ID")
        self.send_header("Access-Control-Expose-Headers", "Last-Event-ID")

        if path.startswith("/events/"):
            task_id = path[8:]  # Remove "/events/"
            self._handle_task_stream(task_id)
        elif path == "/events/system":
            self._handle_system_stream()
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", self.server.sse_service.allowed_origin)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Cache-Control, Last-Event-ID")
        self.end_headers()

    def _handle_task_stream(self, task_id: str):
        """Handle SSE stream for a specific task."""
        client_id = f"sse_{id(self)}_{int(time.time() * 1000)}"
        client = self.server.sse_service.register_client(client_id, self.client_address)
        client.task_id = task_id
        
        self.server.sse_service.add_task_client(client_id, task_id)

        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            # Send past events if Last-Event-ID is provided
            last_event_id = self.headers.get("Last-Event-ID")
            if last_event_id:
                self._send_past_events(task_id, int(last_event_id))

            # Keep connection alive and send events
            while self.server.sse_service._running:
                # Check for new events
                with self.server.sse_service._lock:
                    events = self.server.sse_service._event_queue.get(task_id, [])
                    for event in events:
                        if event["id"] > client.last_event_id:
                            self._send_sse_event(event)
                            client.last_event_id = event["id"]
                
                time.sleep(0.1)  # Poll interval

        except Exception as e:
            logger.debug(f"SSE client disconnected: {e}")
        finally:
            self.server.sse_service.remove_client(client_id)

    def _handle_system_stream(self):
        """Handle SSE stream for system events."""
        client_id = f"sse_sys_{id(self)}_{int(time.time() * 1000)}"
        client = self.server.sse_service.register_client(client_id, self.client_address)
        
        self.server.sse_service.add_system_client(client_id)

        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            # Keep connection alive
            while self.server.sse_service._running:
                time.sleep(1)

        except Exception as e:
            logger.debug(f"SSE system client disconnected: {e}")
        finally:
            self.server.sse_service.remove_client(client_id)

    def _send_past_events(self, task_id: str, after_id: int):
        """Send past events after a specific ID."""
        with self.server.sse_service._lock:
            events = self.server.sse_service._event_queue.get(task_id, [])
            for event in events:
                if event["id"] > after_id:
                    self._send_sse_event(event)

    def _send_sse_event(self, event: dict):
        """Send a single SSE event."""
        try:
            self.wfile.write(f"id: {event['id']}\n".encode())
            self.wfile.write(f"event: {event['event']}\n".encode())
            self.wfile.write(f"data: {event['data']}\n\n".encode())
            self.wfile.flush()
        except Exception:
            raise

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def create_sse_service(
    host: str = _DEFAULT_SSE_HOST,
    port: int = _DEFAULT_SSE_PORT,
) -> SSEService:
    """Factory function to create an SSE service."""
    return SSEService(host=host, port=port)
