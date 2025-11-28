import { Card } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { Zap, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import type { PartObject } from "../../services/types";
import type { SignalIntegrityAnalysis } from "../../services/analysisApi";

interface SignalIntegrityPanelProps {
  signalIntegrity: SignalIntegrityAnalysis | null;
  parts: PartObject[];
  onPartAdd?: (part: PartObject) => void;
}

export default function SignalIntegrityPanel({ signalIntegrity, parts, onPartAdd }: SignalIntegrityPanelProps) {
  if (!signalIntegrity) {
    return (
      <div className="p-6 text-center text-neutral-blue">
        No signal integrity data available
      </div>
    );
  }

  const highSpeedSignals = signalIntegrity.high_speed_signals || [];
  const impedanceIssues = signalIntegrity.impedance_recommendations || [];
  const hasIssues = impedanceIssues.length > 0;

  return (
    <div className="space-y-4">
      {/* High-Speed Signals */}
      {highSpeedSignals.length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-5 h-5 text-yellow-400" />
            <h3 className="text-lg font-semibold text-white">High-Speed Signal Analysis</h3>
          </div>
          <div className="space-y-3">
            {highSpeedSignals.map((signal, idx) => (
              <div key={idx} className={`p-3 rounded ${
                signal.impedance_ok ? "bg-green-900/20 border border-green-500/50" : "bg-red-900/20 border border-red-500/50"
              }`}>
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-white mb-1">
                      {signal.name} - {signal.interface}
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-neutral-blue">Calculated:</span>{" "}
                        <span className="text-white">{signal.calculated_impedance_ohms}Ω</span>
                      </div>
                      <div>
                        <span className="text-neutral-blue">Required:</span>{" "}
                        <span className="text-white">{signal.required_impedance_ohms}Ω</span>
                      </div>
                    </div>
                    {signal.recommendation && (
                      <div className="text-xs text-neutral-blue mt-2">
                        <strong>Recommendation:</strong> {signal.recommendation}
                      </div>
                    )}
                  </div>
                  {signal.impedance_ok ? (
                    <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Impedance Issues */}
      {impedanceIssues.length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <h3 className="text-lg font-semibold text-white">Impedance Control Issues</h3>
          </div>
          <div className="space-y-2">
            {impedanceIssues.map((issue, idx) => (
              <div key={idx} className="p-3 bg-red-900/20 border border-red-500/50 rounded">
                <div className="text-sm font-medium text-white mb-2">
                  {issue.part} - {issue.interface}
                </div>
                <div className="text-xs text-neutral-blue space-y-1">
                  <div><strong>Current Impedance:</strong> {issue.current_impedance}Ω</div>
                  <div><strong>Required Impedance:</strong> {issue.required_impedance}Ω</div>
                  <div className="text-red-300 mt-2">{issue.recommendation}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* EMI/EMC Recommendations */}
      {signalIntegrity.emi_emc_recommendations && signalIntegrity.emi_emc_recommendations.length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-3">EMI/EMC Recommendations</h3>
          <div className="space-y-2">
            {signalIntegrity.emi_emc_recommendations.map((rec, idx) => (
              <div key={idx} className="p-2 bg-blue-900/20 border border-blue-500/50 rounded text-sm text-blue-300">
                {rec}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Routing Recommendations */}
      {signalIntegrity.routing_recommendations && signalIntegrity.routing_recommendations.length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-3">Routing Recommendations</h3>
          <div className="space-y-2">
            {signalIntegrity.routing_recommendations.map((rec, idx) => (
              <div key={idx} className="p-2 bg-zinc-900/50 rounded text-sm text-neutral-blue">
                {rec}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Decoupling Analysis */}
      {signalIntegrity.decoupling_analysis && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <h3 className="text-lg font-semibold text-white">Decoupling Analysis</h3>
            {signalIntegrity.decoupling_analysis.adequate ? (
              <CheckCircle2 className="w-5 h-5 text-green-400" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-yellow-400" />
            )}
          </div>
          {signalIntegrity.decoupling_analysis.recommendations && 
           signalIntegrity.decoupling_analysis.recommendations.length > 0 && (
            <div className="space-y-2">
              {signalIntegrity.decoupling_analysis.recommendations.map((rec, idx) => (
                <div key={idx} className="p-2 bg-yellow-900/20 border border-yellow-500/50 rounded text-sm text-yellow-300">
                  {rec}
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {!hasIssues && highSpeedSignals.length === 0 && (
        <Card className="p-6 bg-dark-surface border-dark-border text-center">
          <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto mb-3" />
          <div className="text-lg font-semibold text-white mb-2">Signal Integrity: Pass</div>
          <div className="text-sm text-neutral-blue">
            No signal integrity issues detected
          </div>
        </Card>
      )}
    </div>
  );
}


