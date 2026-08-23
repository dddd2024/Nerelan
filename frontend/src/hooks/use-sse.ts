import { useEffect, useRef, useCallback, useState } from "react";

interface SSEEvent {
  id: number;
  event: string;
  data: any;
  timestamp: number;
}

interface UseSSEOptions {
  url?: string;
  task_id?: string;
  lastEventId?: number;
  onEvent?: (event: SSEEvent) => void;
  onOpen?: () => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

interface UseSSEReturn {
  isConnected: boolean;
  lastEvent: SSEEvent | null;
  events: SSEEvent[];
  error: string | null;
  connect: () => void;
  disconnect: () => void;
  clearEvents: () => void;
}

export function useSSE(options: UseSSEOptions = {}): UseSSEReturn {
  const {
    url = "http://127.0.0.1:8768",
    task_id,
    lastEventId,
    onEvent,
    onOpen,
    onError,
    autoReconnect = true,
    reconnectInterval = 3000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null);
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const endpoint = task_id 
      ? `${url}/events/${task_id}`
      : `${url}/events/system`;

    const eventSource = new EventSource(endpoint);
    eventSourceRef.current = eventSource;

    // Set Last-Event-ID if provided
    if (lastEventId !== undefined) {
      // EventSource doesn't support setting Last-Event-ID directly
      // We'll handle this server-side
    }

    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
      onOpen?.();
    };

    eventSource.onmessage = (event) => {
      const sseEvent: SSEEvent = {
        id: parseInt(event.lastEventId || "0", 10),
        event: "message",
        data: JSON.parse(event.data),
        timestamp: Date.now(),
      };
      
      setLastEvent(sseEvent);
      setEvents((prev) => [...prev.slice(-99), sseEvent]); // Keep last 100 events
      onEvent?.(sseEvent);
    };

    // Handle named events
    const eventTypes = [
      "task_update",
      "agent_status",
      "log_entry",
      "progress",
      "result",
      "error",
      "complete",
    ];

    eventTypes.forEach((eventType) => {
      eventSource.addEventListener(eventType, (event) => {
        const messageEvent = event as MessageEvent;
        const sseEvent: SSEEvent = {
          id: parseInt(messageEvent.lastEventId || "0", 10),
          event: eventType,
          data: JSON.parse(messageEvent.data),
          timestamp: Date.now(),
        };
        
        setLastEvent(sseEvent);
        setEvents((prev) => [...prev.slice(-99), sseEvent]);
        onEvent?.(sseEvent);
      });
    });

    eventSource.onerror = (event) => {
      setIsConnected(false);
      setError("Connection lost");
      onError?.(event);
      
      if (autoReconnect) {
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, reconnectInterval);
      }
    };
  }, [url, task_id, lastEventId, onEvent, onOpen, onError, autoReconnect, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setLastEvent(null);
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastEvent,
    events,
    error,
    connect,
    disconnect,
    clearEvents,
  };
}

export function useTaskSSE(taskId: string | null) {
  const [taskUpdate, setTaskUpdate] = useState<any>(null);
  const [agentStatus, setAgentStatus] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [progress, setProgress] = useState<number>(0);
  const [result, setResult] = useState<any>(null);

  const { isConnected, lastEvent, events, error } = useSSE({
    task_id: taskId || undefined,
    onEvent: (event) => {
      switch (event.event) {
        case "task_update":
          setTaskUpdate(event.data);
          break;
        case "agent_status":
          setAgentStatus(event.data);
          break;
        case "log_entry":
          setLogs((prev) => [...prev, event.data]);
          break;
        case "progress":
          setProgress(event.data.progress || 0);
          break;
        case "result":
          setResult(event.data);
          break;
        case "complete":
          setResult(event.data);
          break;
      }
    },
  });

  return {
    isConnected,
    lastEvent,
    events,
    error,
    taskUpdate,
    agentStatus,
    logs,
    progress,
    result,
  };
}
