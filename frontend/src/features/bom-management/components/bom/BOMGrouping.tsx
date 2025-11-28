/**
 * BOM Grouping Component
 * Group and organize BOM by various criteria
 */

import React, { useMemo, useState } from "react";
import { Card } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import {
  Folder,
  FolderOpen,
  ChevronRight,
  Package,
  Building2,
  Tag,
} from "lucide-react";
import type { PartObject } from "../../services/types";
import { normalizePrice, normalizeQuantity } from "../../utils/partNormalizer";

interface BOMGroupingProps {
  parts: PartObject[];
  groupBy: "category" | "manufacturer" | "package" | "none";
  onGroupChange?: (groupBy: BOMGroupingProps["groupBy"]) => void;
}

export default function BOMGrouping({
  parts,
  groupBy,
  onGroupChange,
}: BOMGroupingProps) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  const groupedParts = useMemo(() => {
    if (groupBy === "none") {
      return { "All Parts": parts };
    }

    const groups: Record<string, PartObject[]> = {};
    parts.forEach((part) => {
      const key = part[groupBy] || "Unknown";
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(part);
    });

    return groups;
  }, [parts, groupBy]);

  const toggleGroup = (groupName: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupName)) {
      newExpanded.delete(groupName);
    } else {
      newExpanded.add(groupName);
    }
    setExpandedGroups(newExpanded);
  };

  const getGroupIcon = () => {
    switch (groupBy) {
      case "category":
        return <Tag className="w-4 h-4" />;
      case "manufacturer":
        return <Building2 className="w-4 h-4" />;
      case "package":
        return <Package className="w-4 h-4" />;
      default:
        return <Folder className="w-4 h-4" />;
    }
  };

  const totalCost = (groupParts: PartObject[]) => {
    return groupParts.reduce(
      (sum, part) => sum + normalizePrice(part.price) * normalizeQuantity(part.quantity),
      0
    );
  };

  return (
    <Card className="bg-dark-surface border-dark-border p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {getGroupIcon()}
          <h3 className="text-lg font-semibold text-white">BOM Groups</h3>
          <Badge variant="outline" className="text-xs">
            {Object.keys(groupedParts).length} group(s)
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant={groupBy === "category" ? "default" : "outline"}
            onClick={() => onGroupChange?.("category")}
            className="text-xs"
          >
            Category
          </Button>
          <Button
            size="sm"
            variant={groupBy === "manufacturer" ? "default" : "outline"}
            onClick={() => onGroupChange?.("manufacturer")}
            className="text-xs"
          >
            Manufacturer
          </Button>
          <Button
            size="sm"
            variant={groupBy === "package" ? "default" : "outline"}
            onClick={() => onGroupChange?.("package")}
            className="text-xs"
          >
            Package
          </Button>
          <Button
            size="sm"
            variant={groupBy === "none" ? "default" : "outline"}
            onClick={() => onGroupChange?.("none")}
            className="text-xs"
          >
            None
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        {Object.entries(groupedParts).map(([groupName, groupParts]) => {
          const isExpanded = expandedGroups.has(groupName);
          const groupCost = totalCost(groupParts);

          return (
            <div
              key={groupName}
              className="border border-dark-border rounded bg-dark-bg"
            >
              <button
                onClick={() => toggleGroup(groupName)}
                className="w-full flex items-center justify-between p-3 hover:bg-zinc-900/50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <ChevronRight
                    className={`w-4 h-4 text-neutral-blue transition-transform ${
                      isExpanded ? "rotate-90" : ""
                    }`}
                  />
                  {isExpanded ? (
                    <FolderOpen className="w-4 h-4 text-neutral-blue" />
                  ) : (
                    <Folder className="w-4 h-4 text-neutral-blue" />
                  )}
                  <span className="text-sm font-medium text-white">
                    {groupName}
                  </span>
                  <Badge variant="outline" className="text-xs">
                    {groupParts.length}
                  </Badge>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-neutral-blue">
                    ${groupCost.toFixed(2)}
                  </span>
                </div>
              </button>

              {isExpanded && (
                <div className="p-3 pt-0 border-t border-dark-border">
                  <div className="space-y-1">
                    {groupParts.map((part) => (
                      <div
                        key={part.componentId}
                        className="flex items-center justify-between p-2 bg-zinc-900/30 rounded text-sm"
                      >
                        <div className="flex-1">
                          <div className="text-white font-mono text-xs">
                            {part.mpn}
                          </div>
                          <div className="text-neutral-blue text-xs">
                            {part.manufacturer}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-white text-xs">
                            Qty: {part.quantity || 1}
                          </div>
                          <div className="text-neutral-blue text-xs">
                            ${(normalizePrice(part.price) * normalizeQuantity(part.quantity)).toFixed(2)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}

