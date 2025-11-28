import React, { useState } from "react";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { 
  GitCompare, 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  AlertTriangle,
  CheckCircle2,
  XCircle
} from "lucide-react";
import type { PartObject } from "../services/types";

interface DesignComparisonProps {
  currentDesign: {
    parts: PartObject[];
    connections?: any[];
    query?: string;
  };
  previousDesign?: {
    parts: PartObject[];
    connections?: any[];
    query?: string;
  };
  onRevert?: () => void;
}

export default function DesignComparison({
  currentDesign,
  previousDesign,
  onRevert,
}: DesignComparisonProps) {
  const [selectedMetric, setSelectedMetric] = useState<"cost" | "parts" | "power">("cost");

  if (!previousDesign) {
    return (
      <Card className="p-4 bg-dark-surface border-dark-border">
        <div className="text-center py-8 text-zinc-400">
          <GitCompare className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No previous design to compare with</p>
          <p className="text-xs mt-2">Load a previous design to see comparisons</p>
        </div>
      </Card>
    );
  }

  // Calculate differences
  const currentPartCount = currentDesign.parts.length;
  const previousPartCount = previousDesign.parts.length;
  const partCountDiff = currentPartCount - previousPartCount;

  const currentCost = currentDesign.parts.reduce(
    (sum, p) => sum + (p.price || 0) * (p.quantity || 1),
    0
  );
  const previousCost = previousDesign.parts.reduce(
    (sum, p) => sum + (p.price || 0) * (p.quantity || 1),
    0
  );
  const costDiff = currentCost - previousCost;
  const costDiffPercent = previousCost > 0 ? (costDiff / previousCost) * 100 : 0;

  // Find added/removed parts
  const currentPartIds = new Set(currentDesign.parts.map(p => p.mpn));
  const previousPartIds = new Set(previousDesign.parts.map(p => p.mpn));
  
  const addedParts = currentDesign.parts.filter(p => !previousPartIds.has(p.mpn));
  const removedParts = previousDesign.parts.filter(p => !currentPartIds.has(p.mpn));
  
  // Find modified parts (quantity changes)
  const modifiedParts = currentDesign.parts
    .map(currentPart => {
      const previousPart = previousDesign.parts.find(p => p.mpn === currentPart.mpn);
      if (previousPart && (currentPart.quantity || 1) !== (previousPart.quantity || 1)) {
        return {
          part: currentPart,
          previousQuantity: previousPart.quantity || 1,
          currentQuantity: currentPart.quantity || 1,
        };
      }
      return null;
    })
    .filter(Boolean);

  return (
    <Card className="p-4 bg-dark-surface border-dark-border">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <GitCompare className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Design Comparison</h3>
        </div>
        {onRevert && (
          <Button
            onClick={onRevert}
            size="sm"
            variant="outline"
            className="text-xs"
          >
            Revert to Previous
          </Button>
        )}
      </div>

      {/* Metric Selector */}
      <div className="flex gap-2 mb-4">
        {(["cost", "parts", "power"] as const).map((metric) => (
          <button
            key={metric}
            onClick={() => setSelectedMetric(metric)}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              selectedMetric === metric
                ? "bg-blue-500/20 text-blue-400 border border-blue-500/50"
                : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
            }`}
          >
            {metric.charAt(0).toUpperCase() + metric.slice(1)}
          </button>
        ))}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="p-3 rounded bg-zinc-900/50 border border-zinc-800">
          <div className="text-xs text-zinc-400 mb-1">Parts</div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-semibold text-white">{currentPartCount}</span>
            {partCountDiff !== 0 && (
              <span className={`text-xs flex items-center gap-1 ${
                partCountDiff > 0 ? "text-green-400" : "text-red-400"
              }`}>
                {partCountDiff > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                {Math.abs(partCountDiff)}
              </span>
            )}
          </div>
        </div>

        <div className="p-3 rounded bg-zinc-900/50 border border-zinc-800">
          <div className="text-xs text-zinc-400 mb-1">Cost</div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-semibold text-white">
              ${currentCost.toFixed(2)}
            </span>
            {costDiff !== 0 && (
              <span className={`text-xs flex items-center gap-1 ${
                costDiff < 0 ? "text-green-400" : "text-red-400"
              }`}>
                {costDiff < 0 ? <TrendingDown className="w-3 h-3" /> : <TrendingUp className="w-3 h-3" />}
                {costDiffPercent > 0 ? "+" : ""}{costDiffPercent.toFixed(1)}%
              </span>
            )}
          </div>
        </div>

        <div className="p-3 rounded bg-zinc-900/50 border border-zinc-800">
          <div className="text-xs text-zinc-400 mb-1">Changes</div>
          <div className="text-lg font-semibold text-white">
            {addedParts.length + removedParts.length + modifiedParts.length}
          </div>
        </div>
      </div>

      {/* Changes List */}
      <div className="space-y-2">
        {addedParts.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle2 className="w-4 h-4 text-green-400" />
              <span className="text-sm font-semibold text-green-400">
                Added ({addedParts.length})
              </span>
            </div>
            <div className="space-y-1 ml-6">
              {addedParts.map((part) => (
                <div key={part.mpn} className="text-xs text-zinc-300">
                  + {part.mpn} ({part.quantity || 1}x)
                </div>
              ))}
            </div>
          </div>
        )}

        {removedParts.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <XCircle className="w-4 h-4 text-red-400" />
              <span className="text-sm font-semibold text-red-400">
                Removed ({removedParts.length})
              </span>
            </div>
            <div className="space-y-1 ml-6">
              {removedParts.map((part) => (
                <div key={part.mpn} className="text-xs text-zinc-300">
                  - {part.mpn} (was {part.quantity || 1}x)
                </div>
              ))}
            </div>
          </div>
        )}

        {modifiedParts.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-yellow-400" />
              <span className="text-sm font-semibold text-yellow-400">
                Modified ({modifiedParts.length})
              </span>
            </div>
            <div className="space-y-1 ml-6">
              {modifiedParts.map((change: any) => (
                <div key={change.part.mpn} className="text-xs text-zinc-300">
                  {change.part.mpn}: {change.previousQuantity}x → {change.currentQuantity}x
                </div>
              ))}
            </div>
          </div>
        )}

        {addedParts.length === 0 && removedParts.length === 0 && modifiedParts.length === 0 && (
          <div className="text-center py-4 text-zinc-500 text-sm">
            No changes detected
          </div>
        )}
      </div>
    </Card>
  );
}

