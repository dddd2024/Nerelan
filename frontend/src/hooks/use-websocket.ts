import { useEffect, useRef, useCallback, useState } from "react";

interface WebSocketMessage {
  type: string;
  topic?: string;
  data?: any;
  event?: string;
  [key: string]: any;
}

interface UseWebSocketOptions {
  url?: string;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: any) => void;
  subscribe: (topic: string) => void;
  unsubscribe: (topic: string) => void;
  reconnect: () => void;
  disconnect: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    url = "ws://127.0.0.1:8767",
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const subscriptionsRef = useRef<Set<string>>(new Set());

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        onConnect?.();
        
        // Re-subscribe to previous topics
        subscriptionsRef.current.forEach((topic) => {
          ws.send(JSON.stringify({ type: "subscribe", topic }));
        });
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch (e) {
          console.error("Failed to parse WebSocket message:", e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        onDisconnect?.();
        
        if (reconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        onError?.(error);
      };
    } catch (error) {
      console.error("WebSocket connection error:", error);
    }
  }, [url, reconnect, reconnectInterval, maxReconnectAttempts, onMessage, onConnect, onDisconnect, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const subscribe = useCallback((topic: string) => {
    subscriptionsRef.current.add(topic);
    sendMessage({ type: "subscribe", topic });
  }, [sendMessage]);

  const unsubscribe = useCallback((topic: string) => {
    subscriptionsRef.current.delete(topic);
    sendMessage({ type: "unsubscribe", topic });
  }, [sendMessage]);

  const reconnectFn = useCallback(() => {
    disconnect();
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect, disconnect]);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    subscribe,
    unsubscribe,
    reconnect: reconnectFn,
    disconnect,
  };
}

export function useTaskUpdates(taskId: string | null) {
  const [taskUpdate, setTaskUpdate] = useState<any>(null);
  const [agentStatus, setAgentStatus] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);

  const { isConnected, subscribe, unsubscribe } = useWebSocket({
    onMessage: (message) => {
      if (message.type === "broadcast") {
        if (message.event === "task_update" && message.task_id === taskId) {
          setTaskUpdate(message);
        } else if (message.event === "agent_status" && message.task_id === taskId) {
          setAgentStatus(message);
        } else if (message.event === "log_entry" && message.task_id === taskId) {
          setLogs((prev) => [...prev, message]);
        }
      }
    },
  });

  useEffect(() => {
    if (taskId) {
      subscribe(`task:${taskId}`);
      subscribe(`log:${taskId}`);
      return () => {
        unsubscribe(`task:${taskId}`);
        unsubscribe(`log:${taskId}`);
      };
    }
  }, [taskId, subscribe, unsubscribe]);

  return {
    isConnected,
    taskUpdate,
    agentStatus,
    logs,
  };
}

export function useSystemUpdates() {
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [announcements, setAnnouncements] = useState<any[]>([]);

  const { isConnected, subscribe } = useWebSocket({
    onMessage: (message) => {
      if (message.type === "broadcast" && message.topic === "system") {
        if (message.event === "system_announcement") {
          setAnnouncements((prev) => [...prev, message]);
        } else {
          setSystemStatus(message);
        }
      }
    },
  });

  useEffect(() => {
    subscribe("system");
  }, [subscribe]);

  return {
    isConnected,
    systemStatus,
    announcements,
  };
}
