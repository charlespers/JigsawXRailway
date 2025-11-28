import React from "react";
import { Card } from "../../shared/components/ui/card";
import { Badge } from "../../shared/components/ui/badge";
import { Activity, CheckCircle2, AlertTriangle, XCircle, TrendingUp } from "lucide-react";

interface HealthBreakdown {
  validation: {
    score: number;
    status: string;
    errors: number;
    warnings: number;
  };
  supply_chain: {
    score: number;
    status: string;
    risk_score: number;
  };
  manufacturing: {
    score: number;
    status: string;
    readiness: string;
  };
  thermal: {
    score: number;
    status: string;
    critical_issues: number;
    warnings: number;
  };
  cost: {
    score: number;
    status: string;
    optimization_opportunities: number;
  };
}

interface DesignHealthScoreProps {
  healthScore: number;
  healthLevel: string;
  healthBreakdown?: HealthBreakdown;
}

export default function DesignHealthScore({
  healthScore,
  healthLevel,
  healthBreakdown,
}: DesignHealthScoreProps) {
  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-green-400";
    if (score >= 75) return "text-green-300";
    if (score >= 60) return "text-yellow-400";
    if (score >= 40) return "text-orange-400";
    return "text-red-400";
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 90) return "bg-green-500/20";
    if (score >= 75) return "bg-green-500/15";
    if (score >= 60) return "bg-yellow-500/20";
    if (score >= 40) return "bg-orange-500/20";
    return "bg-red-500/20";
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "excellent":
        return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case "good":
        return <TrendingUp className="w-4 h-4 text-green-300" />;
      case "needs_improvement":
        return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
      default:
        return <XCircle className="w-4 h-4 text-red-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      excellent: "bg-green-500/20 text-green-400 border-green-500/50",
      good: "bg-green-500/15 text-green-300 border-green-500/40",
      needs_improvement: "bg-yellow-500/20 text-yellow-400 border-yellow-500/50",
      ready: "bg-green-500/20 text-green-400 border-green-500/50",
      not_ready: "bg-red-500/20 text-red-400 border-red-500/50",
      unknown: "bg-zinc-500/20 text-zinc-400 border-zinc-500/50",
    };
    return variants[status as keyof typeof variants] || variants.unknown;
  };

  return (
    <Card className="p-4 bg-dark-surface border-dark-border">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Design Health</h3>
        </div>
        <Badge className={getStatusBadge(healthLevel.toLowerCase().replace(" ", "_"))}>
          {healthLevel}
        </Badge>
      </div>

      {/* Overall Score */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-zinc-400">Overall Health Score</span>
          <span className={`text-2xl font-bold ${getScoreColor(healthScore)}`}>
            {healthScore.toFixed(1)}
          </span>
        </div>
        <div className="w-full bg-zinc-800 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${getScoreBgColor(healthScore)}`}
            style={{ width: `${healthScore}%` }}
          />
        </div>
      </div>

      {/* Breakdown by Category */}
      {healthBreakdown && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-zinc-300">Category Breakdown</h4>
          
          {/* Validation */}
          <div className="flex items-center justify-between p-2 rounded bg-zinc-900/50">
            <div className="flex items-center gap-2">
              {getStatusIcon(healthBreakdown.validation.status)}
              <span className="text-sm text-zinc-300">Validation</span>
            </div>
            <div className="flex items-center gap-3">
              {healthBreakdown.validation.errors > 0 && (
                <span className="text-xs text-red-400">{healthBreakdown.validation.errors} errors</span>
              )}
              {healthBreakdown.validation.warnings > 0 && (
                <span className="text-xs text-yellow-400">{healthBreakdown.validation.warnings} warnings</span>
              )}
              <span className={`text-sm font-semibold ${getScoreColor(healthBreakdown.validation.score)}`}>
                {healthBreakdown.validation.score.toFixed(0)}
              </span>
            </div>
          </div>

          {/* Supply Chain */}
          <div className="flex items-center justify-between p-2 rounded bg-zinc-900/50">
            <div className="flex items-center gap-2">
              {getStatusIcon(healthBreakdown.supply_chain.status)}
              <span className="text-sm text-zinc-300">Supply Chain</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-zinc-500">Risk: {healthBreakdown.supply_chain.risk_score}</span>
              <span className={`text-sm font-semibold ${getScoreColor(healthBreakdown.supply_chain.score)}`}>
                {healthBreakdown.supply_chain.score.toFixed(0)}
              </span>
            </div>
          </div>

          {/* Manufacturing */}
          <div className="flex items-center justify-between p-2 rounded bg-zinc-900/50">
            <div className="flex items-center gap-2">
              {getStatusIcon(healthBreakdown.manufacturing.readiness)}
              <span className="text-sm text-zinc-300">Manufacturing</span>
            </div>
            <div className="flex items-center gap-3">
              <Badge className={getStatusBadge(healthBreakdown.manufacturing.readiness)}>
                {healthBreakdown.manufacturing.readiness}
              </Badge>
              <span className={`text-sm font-semibold ${getScoreColor(healthBreakdown.manufacturing.score)}`}>
                {healthBreakdown.manufacturing.score.toFixed(0)}
              </span>
            </div>
          </div>

          {/* Thermal */}
          <div className="flex items-center justify-between p-2 rounded bg-zinc-900/50">
            <div className="flex items-center gap-2">
              {getStatusIcon(healthBreakdown.thermal.status)}
              <span className="text-sm text-zinc-300">Thermal</span>
            </div>
            <div className="flex items-center gap-3">
              {healthBreakdown.thermal.critical_issues > 0 && (
                <span className="text-xs text-red-400">{healthBreakdown.thermal.critical_issues} critical</span>
              )}
              {healthBreakdown.thermal.warnings > 0 && (
                <span className="text-xs text-yellow-400">{healthBreakdown.thermal.warnings} warnings</span>
              )}
              <span className={`text-sm font-semibold ${getScoreColor(healthBreakdown.thermal.score)}`}>
                {healthBreakdown.thermal.score.toFixed(0)}
              </span>
            </div>
          </div>

          {/* Cost */}
          <div className="flex items-center justify-between p-2 rounded bg-zinc-900/50">
            <div className="flex items-center gap-2">
              {getStatusIcon(healthBreakdown.cost.status)}
              <span className="text-sm text-zinc-300">Cost</span>
            </div>
            <div className="flex items-center gap-3">
              {healthBreakdown.cost.optimization_opportunities > 0 && (
                <span className="text-xs text-blue-400">{healthBreakdown.cost.optimization_opportunities} opportunities</span>
              )}
              <span className={`text-sm font-semibold ${getScoreColor(healthBreakdown.cost.score)}`}>
                {healthBreakdown.cost.score.toFixed(0)}
              </span>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

