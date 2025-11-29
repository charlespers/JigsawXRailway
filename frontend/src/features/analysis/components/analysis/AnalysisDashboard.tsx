/**
 * Comprehensive Analysis Dashboard
 * Unified view of all design analyses
 */

import React, { useState, useEffect } from "react";
import { Card } from "../../../shared/components/ui/card";
import { Badge } from "../../../shared/components/ui/badge";
import { Button } from "../../../shared/components/ui/button";
import {
  DollarSign,
  AlertTriangle,
  Zap,
  Thermometer,
  Shield,
  Package,
  Activity,
  TrendingUp,
  RefreshCw,
} from "lucide-react";
import { useAnalysis } from "../../hooks";
import { useDesignStore } from "../../../design-generation/store/designStore";

interface AnalysisCardProps {
  title: string;
  icon: React.ReactNode;
  value: string | number;
  status: "good" | "warning" | "error";
  onClick?: () => void;
}

function AnalysisCard({ title, icon, value, status, onClick }: AnalysisCardProps) {
  const statusColors = {
    good: "bg-green-500/20 text-green-400 border-green-500/50",
    warning: "bg-yellow-500/20 text-yellow-400 border-yellow-500/50",
    error: "bg-red-500/20 text-red-400 border-red-500/50",
  };

  return (
    <Card
      className={`p-4 bg-dark-surface border ${statusColors[status]} cursor-pointer hover:opacity-80 transition-opacity`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-neutral-blue mb-1">{title}</div>
          <div className="text-lg font-semibold">{value}</div>
        </div>
        <div className="opacity-50">{icon}</div>
      </div>
    </Card>
  );
}

export default function AnalysisDashboard() {
  const { parts, connections } = useDesignStore();
  const { loading, results, runAllAnalyses } = useAnalysis();
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    if (parts.length > 0 && !loading && Object.values(results).every(r => r === null)) {
      runAllAnalyses();
    }
  }, [parts.length]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      if (parts.length > 0) {
        runAllAnalyses();
      }
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, parts.length, runAllAnalyses]);

  const totalCost = results.cost?.total_cost || 0;
  const riskScore = results.supplyChain?.risk_score || 0;
  const totalPower = results.power?.total_power || 0;
  const thermalIssues = results.thermal?.total_thermal_issues || 0;
  const errors = results.validation?.summary?.error_count || 0;
  const warnings = results.validation?.summary?.warning_count || 0;
  const readiness = results.manufacturing?.overall_readiness || "unknown";

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Analysis Dashboard</h2>
          <p className="text-sm text-neutral-blue">
            Comprehensive design analysis and insights
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={autoRefresh ? "bg-neon-teal/20 border-neon-teal" : ""}
          >
            <Activity className={`w-4 h-4 mr-2 ${autoRefresh ? "animate-pulse" : ""}`} />
            Auto-refresh
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={runAllAnalyses}
            disabled={loading || parts.length === 0}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh All
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <AnalysisCard
          title="Total Cost"
          icon={<DollarSign className="w-5 h-5" />}
          value={`$${totalCost.toFixed(2)}`}
          status={totalCost > 100 ? "warning" : "good"}
        />
        <AnalysisCard
          title="Supply Risk"
          icon={<AlertTriangle className="w-5 h-5" />}
          value={`${riskScore.toFixed(0)}%`}
          status={riskScore > 50 ? "error" : riskScore > 25 ? "warning" : "good"}
        />
        <AnalysisCard
          title="Power Consumption"
          icon={<Zap className="w-5 h-5" />}
          value={`${totalPower.toFixed(2)}W`}
          status={totalPower > 10 ? "warning" : "good"}
        />
        <AnalysisCard
          title="Thermal Issues"
          icon={<Thermometer className="w-5 h-5" />}
          value={thermalIssues}
          status={thermalIssues > 0 ? "error" : "good"}
        />
      </div>

      {/* Detailed Analysis Sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Design Validation */}
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-semibold text-white">Design Validation</h3>
          </div>
          {results.validation ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-blue">Errors</span>
                <Badge variant={errors > 0 ? "destructive" : "default"}>
                  {errors}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-blue">Warnings</span>
                <Badge variant={warnings > 0 ? "default" : "default"}>
                  {warnings}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-blue">Compliance Score</span>
                <span className="text-sm font-medium text-white">
                  {results.validation.summary?.compliance_score?.toFixed(0) || 0}%
                </span>
              </div>
            </div>
          ) : (
            <div className="text-sm text-neutral-blue">Run validation to see results</div>
          )}
        </Card>

        {/* Manufacturing Readiness */}
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <Package className="w-5 h-5 text-purple-400" />
            <h3 className="text-lg font-semibold text-white">Manufacturing</h3>
          </div>
          {results.manufacturing ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-blue">Readiness</span>
                <Badge
                  variant={
                    readiness === "ready"
                      ? "default"
                      : readiness === "needs_review"
                      ? "default"
                      : "destructive"
                  }
                >
                  {readiness}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-blue">Complexity Score</span>
                <span className="text-sm font-medium text-white">
                  {results.manufacturing.assembly_complexity?.complexity_score?.toFixed(0) || 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-blue">Test Point Coverage</span>
                <span className="text-sm font-medium text-white">
                  {results.manufacturing.test_point_coverage?.coverage_percentage?.toFixed(0) || 0}%
                </span>
              </div>
            </div>
          ) : (
            <div className="text-sm text-neutral-blue">Run manufacturing analysis to see results</div>
          )}
        </Card>
      </div>

      {loading && (
        <Card className="p-6 bg-dark-surface border-dark-border text-center">
          <RefreshCw className="w-8 h-8 text-neon-teal animate-spin mx-auto mb-2" />
          <p className="text-sm text-neutral-blue">Running analyses...</p>
        </Card>
      )}
    </div>
  );
}

