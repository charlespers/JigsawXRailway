/**
 * Analysis Comparison View
 * Compare multiple analysis results
 */

import React, { useState } from "react";
import { Card } from "../../../shared/components/ui/card";
import { Badge } from "../../../shared/components/ui/badge";
import { Button } from "../../../shared/components/ui/button";
import {
  GitCompare,
  TrendingUp,
  TrendingDown,
  Minus,
  BarChart3,
} from "lucide-react";

interface ComparisonViewProps {
  analyses: Array<{
    name: string;
    data: Record<string, any>;
  }>;
}

export default function ComparisonView({ analyses }: ComparisonViewProps) {
  const [selectedAnalyses, setSelectedAnalyses] = useState<Set<string>>(
    new Set(analyses.map((a) => a.name))
  );

  const toggleAnalysis = (name: string) => {
    const newSelected = new Set(selectedAnalyses);
    if (newSelected.has(name)) {
      newSelected.delete(name);
    } else {
      newSelected.add(name);
    }
    setSelectedAnalyses(newSelected);
  };

  const visibleAnalyses = analyses.filter((a) => selectedAnalyses.has(a.name));

  return (
    <Card className="bg-dark-surface border-dark-border p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <GitCompare className="w-5 h-5 text-neutral-blue" />
          <h3 className="text-lg font-semibold text-white">Compare Analyses</h3>
        </div>
      </div>

      {/* Analysis Selector */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        {analyses.map((analysis) => (
          <Button
            key={analysis.name}
            size="sm"
            variant={selectedAnalyses.has(analysis.name) ? "default" : "outline"}
            onClick={() => toggleAnalysis(analysis.name)}
            className="text-xs"
          >
            {analysis.name}
          </Button>
        ))}
      </div>

      {/* Comparison Table */}
      {visibleAnalyses.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-dark-border">
                <th className="p-2 text-left text-xs font-medium text-neutral-blue">
                  Metric
                </th>
                {visibleAnalyses.map((analysis) => (
                  <th
                    key={analysis.name}
                    className="p-2 text-center text-xs font-medium text-neutral-blue"
                  >
                    {analysis.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Add comparison rows based on analysis data */}
              <tr className="border-b border-dark-border">
                <td className="p-2 text-sm text-white">Status</td>
                {visibleAnalyses.map((analysis) => (
                  <td key={analysis.name} className="p-2 text-center">
                    <Badge variant="outline" className="text-xs">
                      {analysis.data.status || "N/A"}
                    </Badge>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

