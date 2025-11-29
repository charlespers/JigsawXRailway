import { Card } from "../../../shared/components/ui/card";
import { Badge } from "../../../shared/components/ui/badge";
import { Package, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import type { PartObject } from "../../../shared/services/types";
import type { ManufacturingReadiness } from "../../../analysis/services/analysisApi";

interface DFMPanelProps {
  manufacturing: ManufacturingReadiness | null;
  parts: PartObject[];
  onPartAdd?: (part: PartObject) => void;
}

export default function DFMPanel({ manufacturing, parts, onPartAdd }: DFMPanelProps) {
  if (!manufacturing) {
    return (
      <div className="p-6 text-center text-neutral-blue">
        No manufacturing readiness data available
      </div>
    );
  }

  const readiness = manufacturing.overall_readiness;
  const complexityScore = manufacturing.assembly_complexity?.complexity_score || 0;
  const testCoverage = manufacturing.test_point_coverage?.coverage_percentage || 0;

  return (
    <div className="space-y-4">
      {/* Overall Readiness */}
      <Card className="p-4 bg-dark-surface border-dark-border">
        <div className="flex items-center gap-2 mb-4">
          <Package className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Manufacturing Readiness</h3>
          <Badge 
            variant={readiness === "ready" ? "default" : readiness === "needs_review" ? "secondary" : "destructive"}
            className={
              readiness === "ready" ? "bg-green-500/20 text-green-400" :
              readiness === "needs_review" ? "bg-yellow-500/20 text-yellow-400" :
              "bg-red-500/20 text-red-400"
            }
          >
            {readiness === "ready" ? "Ready" : readiness === "needs_review" ? "Needs Review" : "Not Ready"}
          </Badge>
        </div>

        {/* Assembly Complexity */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-neutral-blue">Assembly Complexity Score</span>
            <span className="text-sm font-semibold text-white">{complexityScore}/10</span>
          </div>
          <div className="w-full bg-zinc-800 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all ${
                complexityScore <= 5 ? "bg-green-500" :
                complexityScore <= 7 ? "bg-yellow-500" : "bg-red-500"
              }`}
              style={{ width: `${(complexityScore / 10) * 100}%` }}
            />
          </div>
          {complexityScore > 7 && (
            <div className="text-xs text-yellow-400 mt-1">
              High complexity - may require advanced assembly capabilities
            </div>
          )}
        </div>

        {/* Test Point Coverage */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-neutral-blue">Test Point Coverage</span>
            <span className="text-sm font-semibold text-white">{testCoverage.toFixed(0)}%</span>
          </div>
          <div className="w-full bg-zinc-800 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all ${
                testCoverage >= 80 ? "bg-green-500" :
                testCoverage >= 60 ? "bg-yellow-500" : "bg-red-500"
              }`}
              style={{ width: `${testCoverage}%` }}
            />
          </div>
          {testCoverage < 80 && (
            <div className="text-xs text-yellow-400 mt-1">
              Below recommended 80% coverage - add test points for critical signals
            </div>
          )}
        </div>
      </Card>

      {/* DFM Checks */}
      {manufacturing.dfm_checks && Object.keys(manufacturing.dfm_checks).length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-3">DFM Checks</h3>
          <div className="space-y-2">
            {Object.entries(manufacturing.dfm_checks).map(([checkName, checkResult]: [string, any]) => {
              const check: { status?: string; message?: string } = typeof checkResult === "object" && checkResult !== null ? checkResult : { status: "unknown", message: String(checkResult) };
              const status = check?.status || "unknown";
              
              return (
                <div key={checkName} className="p-3 bg-zinc-900/50 rounded">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-white capitalize">
                      {checkName.replace(/_/g, " ")}
                    </span>
                    {status === "pass" ? (
                      <CheckCircle2 className="w-4 h-4 text-green-400" />
                    ) : status === "fail" ? (
                      <XCircle className="w-4 h-4 text-red-400" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-yellow-400" />
                    )}
                  </div>
                  {check.message && (
                    <div className="text-xs text-neutral-blue mt-1">{check.message}</div>
                  )}
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Recommendations */}
      {manufacturing.recommendations && manufacturing.recommendations.length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-3">Manufacturing Recommendations</h3>
          <div className="space-y-2">
            {manufacturing.recommendations.map((rec: string, idx: number) => (
              <div key={idx} className="p-2 bg-blue-900/20 border border-blue-500/50 rounded text-sm text-blue-300">
                {rec}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}


