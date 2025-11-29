import { Card } from "../../../shared/components/ui/card";
import { Badge } from "../../../shared/components/ui/badge";
import { Thermometer, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import type { PartObject } from "../../../shared/services/types";
import type { ThermalAnalysis } from "../../../analysis/services/analysisApi";

interface ThermalAnalysisPanelProps {
  thermal: ThermalAnalysis | null;
  parts: PartObject[];
  onPartAdd?: (part: PartObject) => void;
}

export default function ThermalAnalysisPanel({ thermal, parts, onPartAdd }: ThermalAnalysisPanelProps) {
  if (!thermal) {
    return (
      <div className="p-6 text-center text-neutral-blue">
        No thermal analysis data available
      </div>
    );
  }

  const thermalIssues = thermal.thermal_issues || [];
  const componentThermal = thermal.component_thermal || {};
  const totalPower = thermal.total_power_dissipation_w || 0;

  return (
    <div className="space-y-4">
      {/* Summary */}
      <Card className="p-4 bg-dark-surface border-dark-border">
        <div className="flex items-center gap-2 mb-4">
          <Thermometer className="w-5 h-5 text-orange-400" />
          <h3 className="text-lg font-semibold text-white">Thermal Analysis Summary</h3>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="p-3 bg-zinc-900/50 rounded">
            <div className="text-sm text-neutral-blue mb-1">Total Power Dissipation</div>
            <div className="text-2xl font-bold text-white">{totalPower.toFixed(2)}W</div>
          </div>
          <div className="p-3 bg-zinc-900/50 rounded">
            <div className="text-sm text-neutral-blue mb-1">Thermal Issues</div>
            <div className="text-2xl font-bold text-red-400">{thermalIssues.length}</div>
          </div>
        </div>
      </Card>

      {/* Critical Thermal Issues */}
      {thermalIssues.length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <XCircle className="w-5 h-5 text-red-400" />
            <h3 className="text-lg font-semibold text-white">Thermal Hotspots</h3>
          </div>
          <div className="space-y-3">
            {thermalIssues.map((issue: any, idx: number) => (
              <div key={idx} className="p-3 bg-red-900/20 border border-red-500/50 rounded">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-white mb-1">
                      {issue.part_id}
                    </div>
                    <div className="text-sm text-red-300 mb-2">{issue.issue}</div>
                    <div className="grid grid-cols-3 gap-2 text-xs text-neutral-blue">
                      <div>
                        <span className="text-neutral-blue">Junction Temp:</span>{" "}
                        <span className="text-white">{issue.junction_temp_c}°C</span>
                      </div>
                      <div>
                        <span className="text-neutral-blue">Max Temp:</span>{" "}
                        <span className="text-white">{issue.max_temp_c}°C</span>
                      </div>
                      <div>
                        <span className="text-neutral-blue">Power:</span>{" "}
                        <span className="text-white">{issue.power_dissipation_w}W</span>
                      </div>
                    </div>
                    {issue.junction_temp_c > issue.max_temp_c && (
                      <div className="text-xs text-red-400 mt-2">
                        <strong>Exceeds limit by:</strong> {(issue.junction_temp_c - issue.max_temp_c).toFixed(1)}°C
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Component Thermal Data */}
      {Object.keys(componentThermal).length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-3">Component Thermal Data</h3>
          <div className="space-y-2">
            {Object.entries(componentThermal).map(([partId, thermalData]: [string, any]) => (
              <div 
                key={partId} 
                className={`p-3 rounded ${
                  thermalData.thermal_ok 
                    ? "bg-green-900/20 border border-green-500/50" 
                    : "bg-yellow-900/20 border border-yellow-500/50"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium text-white">{partId}</div>
                  {thermalData.thermal_ok ? (
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-yellow-400" />
                  )}
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div>
                    <span className="text-neutral-blue">Power:</span>{" "}
                    <span className="text-white">{thermalData.power_dissipation_w}W</span>
                  </div>
                  <div>
                    <span className="text-neutral-blue">Junction:</span>{" "}
                    <span className="text-white">{thermalData.junction_temp_c}°C</span>
                  </div>
                  <div>
                    <span className="text-neutral-blue">Max:</span>{" "}
                    <span className="text-white">{thermalData.max_temp_c}°C</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Recommendations */}
      {thermal.recommendations && thermal.recommendations.length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-3">Thermal Recommendations</h3>
          <div className="space-y-2">
            {thermal.recommendations.map((rec: string, idx: number) => (
              <div key={idx} className="p-2 bg-blue-900/20 border border-blue-500/50 rounded text-sm text-blue-300">
                {rec}
              </div>
            ))}
          </div>
        </Card>
      )}

      {thermalIssues.length === 0 && (
        <Card className="p-6 bg-dark-surface border-dark-border text-center">
          <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto mb-3" />
          <div className="text-lg font-semibold text-white mb-2">Thermal Analysis: Pass</div>
          <div className="text-sm text-neutral-blue">
            All components within thermal limits
          </div>
        </Card>
      )}
    </div>
  );
}


