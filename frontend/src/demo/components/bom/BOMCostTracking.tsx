/**
 * BOM Cost Tracking Component
 * Advanced cost analysis and tracking
 */

import React, { useMemo } from "react";
import { Card } from "../../ui/card";
import { Badge } from "../../ui/badge";
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  PieChart,
  BarChart3,
} from "lucide-react";
import type { PartObject } from "../../services/types";

interface BOMCostTrackingProps {
  parts: PartObject[];
  currency?: string;
}

export default function BOMCostTracking({
  parts,
  currency = "USD",
}: BOMCostTrackingProps) {
  const costAnalysis = useMemo(() => {
    const total = parts.reduce(
      (sum, part) => sum + (part.price || 0) * (part.quantity || 1),
      0
    );

    const byCategory: Record<string, number> = {};
    const byManufacturer: Record<string, number> = {};

    parts.forEach((part) => {
      const partCost = (part.price || 0) * (part.quantity || 1);
      
      const category = part.category || "Uncategorized";
      byCategory[category] = (byCategory[category] || 0) + partCost;
      
      const manufacturer = part.manufacturer || "Unknown";
      byManufacturer[manufacturer] = (byManufacturer[manufacturer] || 0) + partCost;
    });

    const highCostItems = parts
      .map((part) => ({
        part,
        cost: (part.price || 0) * (part.quantity || 1),
      }))
      .sort((a, b) => b.cost - a.cost)
      .slice(0, 5);

    return {
      total,
      byCategory,
      byManufacturer,
      highCostItems,
      averagePartCost: parts.length > 0 ? total / parts.length : 0,
    };
  }, [parts]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
    }).format(amount);
  };

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-neutral-blue">Total Cost</span>
            <DollarSign className="w-5 h-5 text-neon-teal" />
          </div>
          <div className="text-2xl font-bold text-white">
            {formatCurrency(costAnalysis.total)}
          </div>
          <div className="text-xs text-neutral-blue mt-1">
            {parts.length} part(s)
          </div>
        </Card>

        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-neutral-blue">Average Part Cost</span>
            <BarChart3 className="w-5 h-5 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {formatCurrency(costAnalysis.averagePartCost)}
          </div>
          <div className="text-xs text-neutral-blue mt-1">
            Per component
          </div>
        </Card>

        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-neutral-blue">Top Cost Item</span>
            <TrendingUp className="w-5 h-5 text-yellow-400" />
          </div>
          {costAnalysis.highCostItems.length > 0 ? (
            <>
              <div className="text-lg font-semibold text-white">
                {formatCurrency(costAnalysis.highCostItems[0].cost)}
              </div>
              <div className="text-xs text-neutral-blue mt-1 truncate">
                {costAnalysis.highCostItems[0].part.mpn}
              </div>
            </>
          ) : (
            <div className="text-sm text-neutral-blue">No items</div>
          )}
        </Card>
      </div>

      {/* Cost by Category */}
      <Card className="p-4 bg-dark-surface border-dark-border">
        <div className="flex items-center gap-2 mb-4">
          <PieChart className="w-5 h-5 text-neutral-blue" />
          <h3 className="text-lg font-semibold text-white">Cost by Category</h3>
        </div>
        <div className="space-y-2">
          {Object.entries(costAnalysis.byCategory)
            .sort(([, a], [, b]) => b - a)
            .map(([category, cost]) => {
              const percentage = (cost / costAnalysis.total) * 100;
              return (
                <div key={category}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-white">{category}</span>
                    <span className="text-sm font-medium text-white">
                      {formatCurrency(cost)} ({percentage.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="w-full bg-zinc-900 rounded-full h-2">
                    <div
                      className="bg-neon-teal h-2 rounded-full transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
        </div>
      </Card>

      {/* High Cost Items */}
      <Card className="p-4 bg-dark-surface border-dark-border">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-neutral-blue" />
          <h3 className="text-lg font-semibold text-white">High Cost Items</h3>
        </div>
        <div className="space-y-2">
          {costAnalysis.highCostItems.map((item, idx) => (
            <div
              key={item.part.componentId}
              className="flex items-center justify-between p-2 bg-dark-bg rounded border border-dark-border"
            >
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  #{idx + 1}
                </Badge>
                <div>
                  <div className="text-sm font-medium text-white">
                    {item.part.mpn}
                  </div>
                  <div className="text-xs text-neutral-blue">
                    {item.part.manufacturer} • Qty: {item.part.quantity || 1}
                  </div>
                </div>
              </div>
              <div className="text-sm font-semibold text-white">
                {formatCurrency(item.cost)}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

