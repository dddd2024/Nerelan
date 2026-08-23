import * as React from "react";
import { 
  CheckCircle, 
  AlertCircle, 
  AlertTriangle, 
  Info, 
  X,
  Bell
} from "lucide-react";
import { cn } from "@/lib/cn";

export type NotificationType = "success" | "error" | "warning" | "info";

interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number;
  onDismiss?: () => void;
}

interface NotificationContextType {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, "id">) => void;
  dismissNotification: (id: string) => void;
  clearAll: () => void;
}

const NotificationContext = React.createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = React.useState<Notification[]>([]);

  const addNotification = React.useCallback((notification: Omit<Notification, "id">) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newNotification = { ...notification, id };
    
    setNotifications((prev) => [...prev, newNotification]);

    if (notification.duration !== 0) {
      setTimeout(() => {
        setNotifications((prev) => prev.filter((n) => n.id !== id));
      }, notification.duration || 5000);
    }
  }, []);

  const dismissNotification = React.useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const clearAll = React.useCallback(() => {
    setNotifications([]);
  }, []);

  return (
    <NotificationContext.Provider
      value={{ notifications, addNotification, dismissNotification, clearAll }}
    >
      {children}
      <NotificationContainer notifications={notifications} onDismiss={dismissNotification} />
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = React.useContext(NotificationContext);
  if (!context) {
    throw new Error("useNotifications must be used within a NotificationProvider");
  }
  return context;
}

function NotificationContainer({
  notifications,
  onDismiss
}: {
  notifications: Notification[];
  onDismiss: (id: string) => void;
}) {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {notifications.map((notification) => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onDismiss={onDismiss}
        />
      ))}
    </div>
  );
}

function NotificationItem({
  notification,
  onDismiss
}: {
  notification: Notification;
  onDismiss: (id: string) => void;
}) {
  const iconMap = {
    success: <CheckCircle className="h-5 w-5 text-emerald-400" />,
    error: <AlertCircle className="h-5 w-5 text-red-400" />,
    warning: <AlertTriangle className="h-5 w-5 text-amber-300" />,
    info: <Info className="h-5 w-5 text-blue-400" />
  };

  const bgMap = {
    success: "border-emerald-500/30 bg-emerald-500/10",
    error: "border-red-500/30 bg-red-500/10",
    warning: "border-amber-500/30 bg-amber-500/10",
    info: "border-blue-500/30 bg-blue-500/10"
  };

  return (
    <div
      className={cn(
        "flex items-start gap-3 p-4 rounded-xl border shadow-lg backdrop-blur-sm animate-in slide-in-from-right-full",
        bgMap[notification.type]
      )}
    >
      <div className="shrink-0 mt-0.5">{iconMap[notification.type]}</div>
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-medium text-ra-text">{notification.title}</h4>
        {notification.message && (
          <p className="text-sm text-ra-text-secondary mt-1">{notification.message}</p>
        )}
      </div>
      <button
        onClick={() => onDismiss(notification.id)}
        className="shrink-0 p-1 rounded-lg hover:bg-ra-tertiary text-ra-text-tertiary hover:text-ra-text"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

export function NotificationBell() {
  const { notifications } = useNotifications();
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-ra-tertiary text-ra-text-secondary hover:text-ra-text"
      >
        <Bell className="h-5 w-5" />
        {notifications.length > 0 && (
          <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 text-[10px] font-medium text-white flex items-center justify-center">
            {notifications.length}
          </span>
        )}
      </button>
      
      {isOpen && (
        <div className="absolute right-0 top-12 z-50 w-80 rounded-xl border border-ra-border bg-ra-base shadow-lg">
          <div className="p-3 border-b border-ra-border">
            <h3 className="text-sm font-medium text-ra-text">通知</h3>
          </div>
          <div className="max-h-64 overflow-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-sm text-ra-text-tertiary">
                暂无通知
              </div>
            ) : (
              notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onDismiss={() => {}}
                />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
