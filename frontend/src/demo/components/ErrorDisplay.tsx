/**
 * ErrorDisplay Component
 * Enterprise-grade error display with recovery options
 */

import React from "react";
import { AlertCircle, RefreshCw, X, Info, AlertTriangle } from "lucide-react";
import { Button } from "../ui/button";

export interface ErrorDisplayProps {
  error: Error | string;
  title?: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  severity?: "error" | "warning" | "info";
  showDetails?: boolean;
  recoveryActions?: Array<{
    label: string;
    action: () => void;
    variant?: "default" | "outline" | "destructive";
  }>;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  title,
  onRetry,
  onDismiss,
  severity = "error",
  showDetails = false,
  recoveryActions = [],
}) => {
  const errorMessage = typeof error === "string" ? error : error.message;
  const errorStack = typeof error === "string" ? undefined : error.stack;

  const severityConfig = {
    error: {
      icon: AlertCircle,
      bgColor: "bg-red-500/20",
      borderColor: "border-red-500/50",
      textColor: "text-red-400",
      iconColor: "text-red-400",
    },
    warning: {
      icon: AlertTriangle,
      bgColor: "bg-yellow-500/20",
      borderColor: "border-yellow-500/50",
      textColor: "text-yellow-400",
      iconColor: "text-yellow-400",
    },
    info: {
      icon: Info,
      bgColor: "bg-blue-500/20",
      borderColor: "border-blue-500/50",
      textColor: "text-blue-400",
      iconColor: "text-blue-400",
    },
  };

  const config = severityConfig[severity];
  const Icon = config.icon;

  return (
    <div className={`${config.bgColor} ${config.borderColor} border rounded-lg p-4 space-y-3`}>
      <div className="flex items-start gap-3">
        <div className={`flex-shrink-0 w-8 h-8 rounded-full ${config.bgColor} flex items-center justify-center`}>
          <Icon className={`w-4 h-4 ${config.iconColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className={`text-sm font-semibold ${config.textColor} mb-1`}>
            {title || (severity === "error" ? "Error" : severity === "warning" ? "Warning" : "Information")}
          </h3>
          <p className="text-sm text-zinc-300 break-words">{errorMessage}</p>
          {showDetails && errorStack && (
            <details className="mt-2">
              <summary className="text-xs text-zinc-400 cursor-pointer hover:text-zinc-300">
                Technical Details
              </summary>
              <pre className="mt-2 text-xs text-zinc-500 font-mono bg-zinc-950 p-2 rounded overflow-auto max-h-32">
                {errorStack}
              </pre>
            </details>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="flex-shrink-0 text-zinc-400 hover:text-zinc-300 transition-colors"
            aria-label="Dismiss error"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {(onRetry || recoveryActions.length > 0) && (
        <div className="flex gap-2 flex-wrap">
          {onRetry && (
            <Button
              onClick={onRetry}
              size="sm"
              className="bg-emerald-600 hover:bg-emerald-500 text-white"
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Retry
            </Button>
          )}
          {recoveryActions.map((action, idx) => (
            <Button
              key={idx}
              onClick={action.action}
              size="sm"
              variant={action.variant || "outline"}
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
            >
              {action.label}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
};

export default ErrorDisplay;
