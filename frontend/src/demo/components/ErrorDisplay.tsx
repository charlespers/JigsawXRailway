import { AlertCircle, RefreshCw, X, Info } from "lucide-react";
import { Button } from "../ui/button";
import { motion, AnimatePresence } from "motion/react";

export interface ErrorDisplayProps {
  error: string | Error | null;
  onRetry?: () => void;
  onDismiss?: () => void;
  variant?: "error" | "warning" | "info";
  showDetails?: boolean;
  className?: string;
}

/**
 * User-friendly error display component with retry functionality
 */
export default function ErrorDisplay({
  error,
  onRetry,
  onDismiss,
  variant = "error",
  showDetails = false,
  className = "",
}: ErrorDisplayProps) {
  if (!error) return null;

  const errorMessage =
    error instanceof Error ? error.message : String(error);

  const variantStyles = {
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
      icon: AlertCircle,
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

  const styles = variantStyles[variant];
  const Icon = styles.icon;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className={`${styles.bg} ${styles.border} border rounded-lg p-4 ${className}`}
      >
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-0.5">
            <Icon className={`w-5 h-5 ${styles.iconColor}`} />
          </div>
          <div className="flex-1 min-w-0">
            <p className={`text-sm font-medium ${styles.text}`}>
              {errorMessage}
            </p>
            {showDetails && error instanceof Error && error.stack && (
              <details className="mt-2">
                <summary className="text-xs text-zinc-500 cursor-pointer hover:text-zinc-400">
                  Show details
                </summary>
                <pre className="mt-2 text-xs text-zinc-500 font-mono bg-zinc-950 p-2 rounded overflow-auto max-h-32">
                  {error.stack}
                </pre>
              </details>
            )}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {onRetry && (
              <Button
                onClick={onRetry}
                size="sm"
                variant="ghost"
                className={`${styles.text} hover:${styles.bg} h-8 px-2`}
                title="Retry"
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
            )}
            {onDismiss && (
              <Button
                onClick={onDismiss}
                size="sm"
                variant="ghost"
                className="text-zinc-500 hover:text-zinc-400 h-8 px-2"
                title="Dismiss"
              >
                <X className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

