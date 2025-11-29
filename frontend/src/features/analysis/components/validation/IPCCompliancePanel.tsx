import { Card } from "../../../shared/components/ui/card";
import { Badge } from "../../../shared/components/ui/badge";
import { Button } from "../../../shared/components/ui/button";
import { Shield, CheckCircle2, XCircle, AlertTriangle, Info } from "lucide-react";
import type { PartObject } from "../../../shared/services/types";
import type { DesignValidation } from "../../../analysis/services/analysisApi";

interface IPCCompliancePanelProps {
  validation: DesignValidation | null;
  parts: PartObject[];
  onPartAdd?: (part: PartObject) => void;
}

export default function IPCCompliancePanel({ validation, parts, onPartAdd }: IPCCompliancePanelProps) {
  if (!validation) {
    return (
      <div className="p-6 text-center text-neutral-blue">
        No validation data available
      </div>
    );
  }

  const ipcIssues = validation.issues.filter((i: any) => i.category === "ipc_compliance");
  const ipcWarnings = validation.warnings.filter((w: any) => {
    const wObj = typeof w === "string" ? null : w;
    return wObj?.category === "ipc_compliance";
  });

  const ipc7351Compliant = validation.compliance?.ipc_7351 ?? true;
  const ipc2221Compliant = validation.compliance?.ipc_2221 ?? true;

  return (
    <div className="space-y-4">
      {/* Compliance Status */}
      <Card className="p-4 bg-dark-surface border-dark-border">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">IPC Compliance Status</h3>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="p-3 bg-zinc-900/50 rounded">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-neutral-blue">IPC-7351 (Footprints)</span>
              {ipc7351Compliant ? (
                <CheckCircle2 className="w-5 h-5 text-green-400" />
              ) : (
                <XCircle className="w-5 h-5 text-red-400" />
              )}
            </div>
            <div className="text-xs text-neutral-blue">
              {ipc7351Compliant 
                ? "All footprints comply with IPC-7351 standards"
                : "Some footprints missing IPC-7351 designation"}
            </div>
          </div>

          <div className="p-3 bg-zinc-900/50 rounded">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-neutral-blue">IPC-2221 (Design Rules)</span>
              {ipc2221Compliant ? (
                <CheckCircle2 className="w-5 h-5 text-green-400" />
              ) : (
                <XCircle className="w-5 h-5 text-red-400" />
              )}
            </div>
            <div className="text-xs text-neutral-blue">
              {ipc2221Compliant 
                ? "Design follows IPC-2221 guidelines"
                : "Design rule violations detected"}
            </div>
          </div>
        </div>
      </Card>

      {/* Footprint Issues */}
      {ipcIssues.length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <XCircle className="w-5 h-5 text-red-400" />
            <h3 className="text-lg font-semibold text-white">Footprint Compliance Issues</h3>
          </div>
          <div className="space-y-2">
            {ipcIssues.map((issue: any, idx: number) => (
              <div key={idx} className="p-3 bg-red-900/20 border border-red-500/50 rounded">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {issue.component && (
                      <div className="text-sm font-medium text-white mb-1">
                        Component: {issue.component}
                      </div>
                    )}
                    <div className="text-sm text-red-300 mb-2">{issue.message}</div>
                    {issue.current && issue.required && (
                      <div className="text-xs text-neutral-blue space-y-1">
                        <div><strong>Current:</strong> {issue.current}</div>
                        <div><strong>Required:</strong> {issue.required}</div>
                      </div>
                    )}
                    {issue.recommendation && (
                      <div className="text-xs text-neutral-blue mt-2">
                        <strong>Fix:</strong> {issue.recommendation}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Warnings */}
      {ipcWarnings.length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            <h3 className="text-lg font-semibold text-white">IPC Compliance Warnings</h3>
          </div>
          <div className="space-y-2">
            {ipcWarnings.map((warning: any, idx: number) => {
              const warningMessage = typeof warning === "string" ? warning : warning.message;
              const warningComponent = typeof warning === "string" ? undefined : warning.component;
              const warningRecommendation = typeof warning === "string" ? undefined : warning.recommendation;
              return (
                <div key={idx} className="p-3 bg-yellow-900/20 border border-yellow-500/50 rounded">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {warningComponent && (
                        <div className="text-sm font-medium text-white mb-1">
                          {warningComponent}
                        </div>
                      )}
                      <div className="text-sm text-yellow-300 mb-2">{warningMessage}</div>
                      {warningRecommendation && (
                        <div className="text-xs text-neutral-blue">
                          <strong>Recommendation:</strong> {warningRecommendation}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Parts Missing Footprints */}
      {parts.filter(p => !p.footprint).length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <Info className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-semibold text-white">Parts Missing Footprints</h3>
          </div>
          <div className="space-y-2">
            {parts.filter(p => !p.footprint).map((part, idx) => (
              <div key={idx} className="p-2 bg-zinc-900/50 rounded text-sm">
                <div className="text-white">{part.mpn}</div>
                <div className="text-xs text-neutral-blue">
                  Package: {part.package || "Unknown"} - Add IPC-7351 footprint designation
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {ipcIssues.length === 0 && ipcWarnings.length === 0 && parts.filter(p => !p.footprint).length === 0 && (
        <Card className="p-6 bg-dark-surface border-dark-border text-center">
          <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto mb-3" />
          <div className="text-lg font-semibold text-white mb-2">IPC Compliance: Pass</div>
          <div className="text-sm text-neutral-blue">
            All components have IPC-7351 compliant footprints and design follows IPC-2221 guidelines
          </div>
        </Card>
      )}
    </div>
  );
}


