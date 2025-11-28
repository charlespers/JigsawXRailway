/**
 * Reusable Analysis Card Component
 * Standardized card for displaying analysis results
 */

import React from "react";
import { Card } from "../../shared/components/ui/card";
import { Badge } from "../../shared/components/ui/badge";
import { Button } from "../../shared/components/ui/button";
import {
  AlertTriangle,
  CheckCircle2,
  Info,
  XCircle,
  ExternalLink,
} from "lucide-react";

interface AnalysisCardProps {
  title: string;
  icon?: React.ReactNode;
  status: "success" | "warning" | "error" | "info";
  summary: string | React.ReactNode;
  details?: React.ReactNode;
  actions?: Array<{
    label: string;
    onClick: () => void;
    variant?: "default" | "outline";
  }>;
  onExpand?: () => void;
  expanded?: boolean;
}

export default function AnalysisCard({
  title,
  icon,
  status,
  summary,
  details,
  actions,
  onExpand,
  expanded = false,
}: AnalysisCardProps) {
  const statusConfig = {
    success: {
      color: "text-green-400",
      bg: "bg-green-500/10",
      border: "border-green-500/50",
      icon: <CheckCircle2 className="w-5 h-5" />,
    },
    warning: {
      color: "text-yellow-400",
      bg: "bg-yellow-500/10",
      border: "border-yellow-500/50",
      icon: <AlertTriangle className="w-5 h-5" />,
    },
    error: {
      color: "text-red-400",
      bg: "bg-red-500/10",
      border: "border-red-500/50",
      icon: <XCircle className="w-5 h-5" />,
    },
    info: {
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      border: "border-blue-500/50",
      icon: <Info className="w-5 h-5" />,
    },
  };

  const config = statusConfig[status];

  return (
    <Card
      className={`bg-dark-surface border ${config.border} ${
        onExpand ? "cursor-pointer hover:opacity-80" : ""
      } transition-all`}
      onClick={onExpand}
    >
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className={config.color}>
              {icon || config.icon}
            </div>
            <h3 className="text-lg font-semibold text-white">{title}</h3>
          </div>
          {onExpand && (
            <Badge variant="outline" className="text-xs">
              {expanded ? "Collapse" : "Expand"}
            </Badge>
          )}
        </div>

        <div className={`p-3 rounded ${config.bg} mb-3`}>
          <div className="text-sm text-white">{summary}</div>
        </div>

        {expanded && details && (
          <div className="mt-3 pt-3 border-t border-dark-border">
            {details}
          </div>
        )}

        {actions && actions.length > 0 && (
          <div className="flex items-center gap-2 mt-3 pt-3 border-t border-dark-border">
            {actions.map((action, idx) => (
              <Button
                key={idx}
                size="sm"
                variant={action.variant || "outline"}
                onClick={(e) => {
                  e.stopPropagation();
                  action.onClick();
                }}
                className="text-xs"
              >
                {action.label}
              </Button>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}

