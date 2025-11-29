import { useState, useEffect } from "react";
import { Card } from "../../shared/components/ui/card";
import { Badge } from "../../shared/components/ui/badge";
import { Button } from "../../shared/components/ui/button";
import { 
  CheckCircle2, 
  AlertTriangle, 
  Info, 
  XCircle,
  Shield,
  Zap,
  Thermometer,
  Cpu,
  Package,
  Wrench,
  Plus,
  Download,
  FileText
} from "lucide-react";
import IPCCompliancePanel from "./IPCCompliancePanel";
import DFMPanel from "./DFMPanel";
import SignalIntegrityPanel from "./SignalIntegrityPanel";
import ThermalAnalysisPanel from "./ThermalAnalysisPanel";
import SupplyChainPanel from "./SupplyChainPanel";
import type { PartObject } from "../../shared/services/types";
import {
  validateDesign,
  analyzeManufacturingReadiness,
  analyzeSignalIntegrity,
  analyzeThermal,
  analyzeSupplyChain,
  type DesignValidation,
  type ManufacturingReadiness,
  type SignalIntegrityAnalysis,
  type ThermalAnalysis,
  type SupplyChainAnalysis,
} from "../../analysis/services/analysisApi";

interface DesignValidationPanelProps {
  parts: PartObject[];
  connections?: any[];
  onPartAdd?: (part: PartObject) => void;
}

type TabType = "ipc" | "dfm" | "signal" | "thermal" | "supply" | "summary";

export default function DesignValidationPanel({ 
  parts, 
  connections = [],
  onPartAdd 
}: DesignValidationPanelProps) {
  const [activeTab, setActiveTab] = useState<TabType>("summary");
  const [loading, setLoading] = useState(false);
  const [validation, setValidation] = useState<DesignValidation | null>(null);
  const [manufacturing, setManufacturing] = useState<ManufacturingReadiness | null>(null);
  const [signalIntegrity, setSignalIntegrity] = useState<SignalIntegrityAnalysis | null>(null);
  const [thermal, setThermal] = useState<ThermalAnalysis | null>(null);
  const [supplyChain, setSupplyChain] = useState<SupplyChainAnalysis | null>(null);

  const loadAllAnalyses = async () => {
    if (parts.length === 0) return;
    
    setLoading(true);
    try {
      const bomItems = parts.map(part => ({
        part_data: part,
        quantity: part.quantity || 1,
      }));

      const [val, mfg, si, th, sc] = await Promise.all([
        validateDesign(bomItems, connections).catch(() => null),
        analyzeManufacturingReadiness(bomItems, connections).catch(() => null),
        analyzeSignalIntegrity(bomItems, connections).catch(() => null),
        analyzeThermal(bomItems).catch(() => null),
        analyzeSupplyChain(bomItems).catch(() => null),
      ]);

      setValidation(val);
      setManufacturing(mfg);
      setSignalIntegrity(si);
      setThermal(th);
      setSupplyChain(sc);
    } catch (error) {
      console.error("Failed to load validation analyses:", error);
    } finally {
      setLoading(false);
    }
  };

  // Load analyses when parts change
  useEffect(() => {
    if (parts.length > 0) {
      loadAllAnalyses();
    }
  }, [parts.length]);

  const errorCount = validation?.summary?.error_count || 0;
  const warningCount = validation?.summary?.warning_count || 0;
  const complianceScore = validation?.summary?.compliance_score || 0;

  const tabs = [
    { id: "summary" as TabType, label: "Summary", icon: FileText },
    { id: "ipc" as TabType, label: "IPC Compliance", icon: Shield },
    { id: "dfm" as TabType, label: "DFM", icon: Package },
    { id: "signal" as TabType, label: "Signal Integrity", icon: Zap },
    { id: "thermal" as TabType, label: "Thermal", icon: Thermometer },
    { id: "supply" as TabType, label: "Supply Chain", icon: Cpu },
  ];

  return (
    <div className="space-y-4">
      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-zinc-800 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? "text-neon-teal border-b-2 border-neon-teal bg-zinc-900/70"
                  : "text-neutral-blue hover:text-white"
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {loading && (
          <div className="p-6 text-center text-neutral-blue">
            Loading validation analyses...
          </div>
        )}

        {activeTab === "summary" && (
          <div className="space-y-4">
            {/* Overall Status Card */}
            <Card className="p-6 bg-dark-surface border-dark-border">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Design Validation Summary</h3>
                <Badge 
                  variant={errorCount === 0 ? "default" : "destructive"}
                  className={errorCount === 0 ? "bg-green-500/20 text-green-400" : ""}
                >
                  {errorCount === 0 ? "Valid" : `${errorCount} Error(s)`}
                </Badge>
              </div>

              {/* Compliance Score */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-neutral-blue">Compliance Score</span>
                  <span className="text-sm font-semibold text-white">{complianceScore.toFixed(0)}%</span>
                </div>
                <div className="w-full bg-zinc-800 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all ${
                      complianceScore >= 80 ? "bg-green-500" :
                      complianceScore >= 60 ? "bg-yellow-500" : "bg-red-500"
                    }`}
                    style={{ width: `${complianceScore}%` }}
                  />
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-400">{errorCount}</div>
                  <div className="text-xs text-neutral-blue">Errors</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-400">{warningCount}</div>
                  <div className="text-xs text-neutral-blue">Warnings</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">
                    {parts.length}
                  </div>
                  <div className="text-xs text-neutral-blue">Parts</div>
                </div>
              </div>
            </Card>

            {/* Critical Issues */}
            {validation && validation.issues.length > 0 && (
              <Card className="p-4 bg-dark-surface border-dark-border">
                <div className="flex items-center gap-2 mb-3">
                  <XCircle className="w-5 h-5 text-red-400" />
                  <h3 className="text-lg font-semibold text-white">Critical Issues</h3>
                </div>
                <div className="space-y-2">
                  {validation.issues.slice(0, 5).map((issue, idx) => (
                    <div key={idx} className="p-3 bg-red-900/20 border border-red-500/50 rounded">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="text-sm font-medium text-white mb-1">
                            {issue.component || "Design"}
                          </div>
                          <div className="text-sm text-red-300">{issue.message}</div>
                          {issue.recommendation && (
                            <div className="text-xs text-neutral-blue mt-2">
                              <strong>Fix:</strong> {issue.recommendation}
                            </div>
                          )}
                        </div>
                        {issue.fixable && onPartAdd && (
                          <Button
                            size="sm"
                            variant="outline"
                            className="ml-2 h-7 px-2 text-xs border-red-500/50 text-red-400 hover:bg-red-500/20"
                          >
                            <Wrench className="w-3 h-3 mr-1" />
                            Fix
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Warnings */}
            {validation && validation.warnings.length > 0 && (
              <Card className="p-4 bg-dark-surface border-dark-border">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-5 h-5 text-yellow-400" />
                  <h3 className="text-lg font-semibold text-white">Warnings</h3>
                </div>
                <div className="space-y-2">
                  {validation.warnings.slice(0, 5).map((warning, idx) => {
                    const warningObj = typeof warning === "string" ? { message: warning } : warning;
                    const warningMessage = typeof warning === "string" ? warning : warning.message;
                    const warningComponent = typeof warning === "string" ? undefined : warning.component;
                    const warningRecommendation = typeof warning === "string" ? undefined : warning.recommendation;
                    const warningFixable = typeof warning === "string" ? false : warning.fixable;
                    return (
                      <div key={idx} className="p-3 bg-yellow-900/20 border border-yellow-500/50 rounded">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            {warningComponent && (
                              <div className="text-sm font-medium text-white mb-1">
                                {warningComponent}
                              </div>
                            )}
                            <div className="text-sm text-yellow-300">{warningMessage}</div>
                            {warningRecommendation && (
                              <div className="text-xs text-neutral-blue mt-2">
                                <strong>Recommendation:</strong> {warningRecommendation}
                              </div>
                            )}
                          </div>
                          {warningFixable && onPartAdd && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="ml-2 h-7 px-2 text-xs border-yellow-500/50 text-yellow-400 hover:bg-yellow-500/20"
                            >
                              <Wrench className="w-3 h-3 mr-1" />
                              Fix
                            </Button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>
            )}
          </div>
        )}

        {activeTab === "ipc" && (
          <IPCCompliancePanel 
            validation={validation}
            parts={parts}
            onPartAdd={onPartAdd}
          />
        )}

        {activeTab === "dfm" && (
          <DFMPanel 
            manufacturing={manufacturing}
            parts={parts}
            onPartAdd={onPartAdd}
          />
        )}

        {activeTab === "signal" && (
          <SignalIntegrityPanel 
            signalIntegrity={signalIntegrity}
            parts={parts}
            onPartAdd={onPartAdd}
          />
        )}

        {activeTab === "thermal" && (
          <ThermalAnalysisPanel 
            thermal={thermal}
            parts={parts}
            onPartAdd={onPartAdd}
          />
        )}

        {activeTab === "supply" && (
          <SupplyChainPanel 
            supplyChain={supplyChain}
            parts={parts}
            onPartAdd={onPartAdd}
          />
        )}
      </div>

      {/* Export Report Button */}
      <div className="flex justify-end pt-4 border-t border-zinc-800">
        <Button
          variant="outline"
          className="text-sm"
          onClick={() => {
            // Export validation report as JSON
            const report = {
              timestamp: new Date().toISOString(),
              parts_count: parts.length,
              validation,
              manufacturing,
              signalIntegrity,
              thermal,
              supplyChain,
            };
            const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `design_validation_${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            URL.revokeObjectURL(url);
          }}
        >
          <Download className="w-4 h-4 mr-2" />
          Export Report
        </Button>
      </div>
    </div>
  );
}

