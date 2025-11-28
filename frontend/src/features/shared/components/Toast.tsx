import React, { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, CheckCircle2, AlertCircle, Info, AlertTriangle } from "lucide-react";
import { Button } from "./ui/button";

export type ToastVariant = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  message: string;
  variant: ToastVariant;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastProps {
  toast: Toast;
  onDismiss: (id: string) => void;
}

const ToastComponent: React.FC<ToastProps> = ({ toast, onDismiss }) => {
  useEffect(() => {
    if (toast.duration && toast.duration > 0) {
      const timer = setTimeout(() => {
        onDismiss(toast.id);
      }, toast.duration);
      return () => clearTimeout(timer);
    }
  }, [toast.id, toast.duration, onDismiss]);

  const variantStyles = {
    success: {
      bg: "bg-green-500/10",
      border: "border-green-500/50",
      text: "text-green-400",
      icon: CheckCircle2,
      iconColor: "text-green-400",
    },
    error: {
      bg: "bg-red-500/10",
      border: "border-red-500/50",
      text: "text-red-400",
      icon: AlertCircle,
      iconColor: "text-red-400",
    },
    warning: {
      bg: "bg-yellow-500/10",
      border: "border-yellow-500/50",
      text: "text-yellow-400",
      icon: AlertTriangle,
      iconColor: "text-yellow-400",
    },
    info: {
      bg: "bg-blue-500/10",
      border: "border-blue-500/50",
      text: "text-blue-400",
      icon: Info,
      iconColor: "text-blue-400",
    },
  };

  const styles = variantStyles[toast.variant];
  const Icon = styles.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      className={`${styles.bg} ${styles.border} border rounded-lg p-4 min-w-[300px] max-w-[500px] shadow-lg`}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          <Icon className={`w-5 h-5 ${styles.iconColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-medium ${styles.text}`}>{toast.message}</p>
          {toast.action && (
            <Button
              onClick={toast.action.onClick}
              size="sm"
              variant="ghost"
              className={`${styles.text} hover:${styles.bg} h-7 px-2 mt-2 text-xs`}
            >
              {toast.action.label}
            </Button>
          )}
        </div>
        <Button
          onClick={() => onDismiss(toast.id)}
          size="sm"
          variant="ghost"
          className="text-zinc-500 hover:text-zinc-400 h-7 w-7 p-0 flex-shrink-0"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>
    </motion.div>
  );
};

interface ToastContainerProps {
  toasts: Toast[];
  onDismiss: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onDismiss }) => {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto">
            <ToastComponent toast={toast} onDismiss={onDismiss} />
          </div>
        ))}
      </AnimatePresence>
    </div>
  );
};

// Hook for managing toasts
export const useToast = () => {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const showToast = (
    message: string,
    variant: ToastVariant = "info",
    duration: number = 5000,
    action?: { label: string; onClick: () => void }
  ) => {
    const id = Math.random().toString(36).substring(7);
    const toast: Toast = { id, message, variant, duration, action };
    setToasts((prev) => [...prev, toast]);
    return id;
  };

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const ToastComponent = () => (
    <ToastContainer toasts={toasts} onDismiss={dismissToast} />
  );

  return { showToast, dismissToast, ToastComponent };
};

export default ToastComponent;

