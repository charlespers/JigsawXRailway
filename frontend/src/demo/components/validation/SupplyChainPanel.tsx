import { Card } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { Cpu, AlertTriangle, CheckCircle2, TrendingUp } from "lucide-react";
import type { PartObject } from "../../services/types";
import type { SupplyChainAnalysis } from "../../services/analysisApi";

interface SupplyChainPanelProps {
  supplyChain: SupplyChainAnalysis | null;
  parts: PartObject[];
  onPartAdd?: (part: PartObject) => void;
}

export default function SupplyChainPanel({ supplyChain, parts, onPartAdd }: SupplyChainPanelProps) {
  if (!supplyChain) {
    return (
      <div className="p-6 text-center text-neutral-blue">
        No supply chain data available
      </div>
    );
  }

  const risks = supplyChain.risks || [];
  const riskScore = supplyChain.risk_score || 0;
  const warnings = supplyChain.warnings || [];
  const recommendations = supplyChain.recommendations || [];

  // Group risks by severity
  const highRisks = risks.filter(r => r.risk_score >= 7);
  const mediumRisks = risks.filter(r => r.risk_score >= 4 && r.risk_score < 7);
  const lowRisks = risks.filter(r => r.risk_score < 4);

  return (
    <div className="space-y-4">
      {/* Risk Score Summary */}
      <Card className="p-4 bg-dark-surface border-dark-border">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Supply Chain Risk Assessment</h3>
        </div>

        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-neutral-blue">Overall Risk Score</span>
            <span className={`text-2xl font-bold ${
              riskScore >= 7 ? "text-red-400" :
              riskScore >= 4 ? "text-yellow-400" : "text-green-400"
            }`}>
              {riskScore.toFixed(1)}/10
            </span>
          </div>
          <div className="w-full bg-zinc-800 rounded-full h-3">
            <div 
              className={`h-3 rounded-full transition-all ${
                riskScore >= 7 ? "bg-red-500" :
                riskScore >= 4 ? "bg-yellow-500" : "bg-green-500"
              }`}
              style={{ width: `${(riskScore / 10) * 100}%` }}
            />
          </div>
          <div className="text-xs text-neutral-blue mt-1">
            {riskScore >= 7 ? "High Risk - Immediate action required" :
             riskScore >= 4 ? "Medium Risk - Review recommended" :
             "Low Risk - Design appears stable"}
          </div>
        </div>

        {/* Risk Breakdown */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div>
            <div className="text-lg font-bold text-red-400">{highRisks.length}</div>
            <div className="text-xs text-neutral-blue">High Risk</div>
          </div>
          <div>
            <div className="text-lg font-bold text-yellow-400">{mediumRisks.length}</div>
            <div className="text-xs text-neutral-blue">Medium Risk</div>
          </div>
          <div>
            <div className="text-lg font-bold text-green-400">{lowRisks.length}</div>
            <div className="text-xs text-neutral-blue">Low Risk</div>
          </div>
        </div>
      </Card>

      {/* High Risk Parts */}
      {highRisks.length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <h3 className="text-lg font-semibold text-white">High Risk Components</h3>
          </div>
          <div className="space-y-3">
            {highRisks.map((risk, idx) => (
              <div key={idx} className="p-3 bg-red-900/20 border border-red-500/50 rounded">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-white mb-1">
                      {risk.part_name} (Qty: {risk.quantity})
                    </div>
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="destructive" className="text-xs">
                        Risk: {risk.risk_score.toFixed(1)}
                      </Badge>
                    </div>
                    <ul className="text-xs text-red-300 list-disc list-inside space-y-1">
                      {risk.risks.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Medium Risk Parts */}
      {mediumRisks.length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            <h3 className="text-lg font-semibold text-white">Medium Risk Components</h3>
          </div>
          <div className="space-y-2">
            {mediumRisks.map((risk, idx) => (
              <div key={idx} className="p-3 bg-yellow-900/20 border border-yellow-500/50 rounded">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-white mb-1">
                      {risk.part_name}
                    </div>
                    <Badge variant="outline" className="text-xs border-yellow-500/50 text-yellow-400 mb-2">
                      Risk: {risk.risk_score.toFixed(1)}
                    </Badge>
                    <ul className="text-xs text-yellow-300 list-disc list-inside">
                      {risk.risks.slice(0, 2).map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Warnings */}
      {warnings.length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-3">Supply Chain Warnings</h3>
          <div className="space-y-2">
            {warnings.map((warning, idx) => (
              <div key={idx} className="p-2 bg-yellow-900/20 border border-yellow-500/50 rounded text-sm text-yellow-300">
                {warning}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-semibold text-white">Recommendations</h3>
          </div>
          <div className="space-y-2">
            {recommendations.map((rec, idx) => (
              <div key={idx} className="p-2 bg-blue-900/20 border border-blue-500/50 rounded text-sm text-blue-300">
                {rec}
              </div>
            ))}
          </div>
        </Card>
      )}

      {risks.length === 0 && (
        <Card className="p-6 bg-dark-surface border-dark-border text-center">
          <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto mb-3" />
          <div className="text-lg font-semibold text-white mb-2">Supply Chain: Stable</div>
          <div className="text-sm text-neutral-blue">
            No significant supply chain risks detected
          </div>
        </Card>
      )}
    </div>
  );
}

