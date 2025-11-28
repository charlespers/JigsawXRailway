import { useState, useEffect } from "react";
import { 
  DollarSign, AlertTriangle, CheckCircle2, Zap, 
  TrendingDown, Shield, Activity, Wrench, Plus
} from "lucide-react";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import type { PartObject } from "../services/types";
import {
  analyzeCost,
  analyzeSupplyChain,
  calculatePower,
  validateDesign,
  type CostAnalysis,
  type SupplyChainAnalysis,
  type PowerAnalysis,
  type DesignValidation,
} from "../services/analysisApi";
// Helper function to convert backend part data to PartObject
function convertPartDataToPartObject(partData: any): PartObject {
  // Generate a unique componentId for suggested parts (auto-fix suggestions)
  // Use the part ID or MPN as the componentId, prefixed with "suggested_" to distinguish
  const componentId = partData.componentId || 
                      partData.id || 
                      partData.mfr_part_number || 
                      `suggested_${partData.mfr_part_number || partData.id || Date.now()}`;
  
  return {
    componentId, // CRITICAL: Required field for PartObject
    mpn: partData.mfr_part_number || partData.id || "",
    manufacturer: partData.manufacturer || "",
    description: partData.description || "",
    price: partData.cost_estimate?.value || 0,
    currency: partData.cost_estimate?.currency || "USD",
    voltage: partData.supply_voltage_range 
      ? `${partData.supply_voltage_range.min || ""}V ~ ${partData.supply_voltage_range.max || ""}V`
      : undefined,
    package: partData.package || "",
    interfaces: partData.interface_type || [],
    datasheet: partData.datasheet_url || "",
    quantity: 1,
    category: partData.category,
    footprint: partData.footprint,
    lifecycle_status: partData.lifecycle_status,
    availability_status: partData.availability_status,
  };
}

interface BOMInsightsProps {
  parts: PartObject[];
  connections?: any[];
  onPartAdd?: (part: PartObject) => void;
}

export default function BOMInsights({ parts, connections = [], onPartAdd }: BOMInsightsProps) {
  const [costAnalysis, setCostAnalysis] = useState<CostAnalysis | null>(null);
  const [supplyChainAnalysis, setSupplyChainAnalysis] = useState<SupplyChainAnalysis | null>(null);
  const [powerAnalysis, setPowerAnalysis] = useState<PowerAnalysis | null>(null);
  const [designValidation, setDesignValidation] = useState<DesignValidation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (parts.length === 0) return;
    
    loadAnalyses();
  }, [parts]);

  const loadAnalyses = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Convert parts to BOM items format
      const bomItems = parts.map(part => ({
        part_data: part,
        quantity: part.quantity || 1,
      }));

      // Load all analyses in parallel
      const [cost, supplyChain, power, validation] = await Promise.all([
        analyzeCost(bomItems).catch(() => null),
        analyzeSupplyChain(bomItems).catch(() => null),
        calculatePower(bomItems).catch(() => null),
        validateDesign(bomItems, connections).catch(() => null),
      ]);

      setCostAnalysis(cost);
      setSupplyChainAnalysis(supplyChain);
      setPowerAnalysis(power);
      setDesignValidation(validation);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load analyses");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 text-center text-neutral-blue">
        Loading insights...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center text-red-400">
        Error: {error}
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="w-5 h-5 text-neon-teal" />
            <span className="text-sm text-neutral-blue">Total Cost</span>
          </div>
          <div className="text-2xl font-bold text-white">
            ${costAnalysis?.total_cost.toFixed(2) || "0.00"}
          </div>
        </Card>

        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            <span className="text-sm text-neutral-blue">Risk Score</span>
          </div>
          <div className="text-2xl font-bold text-white">
            {supplyChainAnalysis?.risk_score.toFixed(0) || "0"}
          </div>
        </Card>

        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-5 h-5 text-yellow-400" />
            <span className="text-sm text-neutral-blue">Total Power</span>
          </div>
          <div className="text-2xl font-bold text-white">
            {powerAnalysis?.total_power.toFixed(2) || "0.00"}W
          </div>
        </Card>

        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="w-5 h-5 text-green-400" />
            <span className="text-sm text-neutral-blue">Status</span>
          </div>
          <div className="text-lg font-bold">
            {designValidation?.valid ? (
              <span className="text-green-400">Valid</span>
            ) : (
              <span className="text-red-400">Issues</span>
            )}
          </div>
        </Card>
      </div>

      {/* Cost Optimization */}
      {costAnalysis && costAnalysis.optimization_opportunities.length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <TrendingDown className="w-5 h-5 text-neon-teal" />
            <h3 className="text-lg font-semibold text-white">Cost Optimization</h3>
          </div>
          <div className="space-y-2">
            {costAnalysis.optimization_opportunities.slice(0, 5).map((opp, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-dark-bg rounded">
                <div>
                  <div className="text-sm text-white">{opp.part_name}</div>
                  <div className="text-xs text-neutral-blue">
                    → {opp.alternative.name}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-green-400">
                    Save ${opp.total_savings.toFixed(2)}
                  </div>
                  <div className="text-xs text-neutral-blue">
                    ${opp.current_cost.toFixed(2)} → ${opp.alternative.cost.toFixed(2)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Supply Chain Risks */}
      {supplyChainAnalysis && supplyChainAnalysis.risks.length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-5 h-5 text-yellow-400" />
            <h3 className="text-lg font-semibold text-white">Supply Chain Risks</h3>
          </div>
          <div className="space-y-2">
            {supplyChainAnalysis.risks.slice(0, 5).map((risk, idx) => (
              <div key={idx} className="p-2 bg-dark-bg rounded">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-white">{risk.part_name}</span>
                  <Badge variant="destructive">
                    Risk: {risk.risk_score.toFixed(0)}
                  </Badge>
                </div>
                <ul className="text-xs text-neutral-blue list-disc list-inside">
                  {risk.risks.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Design Validation Issues with Auto-Fix */}
      {designValidation && (!designValidation.valid || designValidation.warnings.length > 0) && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <h3 className="text-lg font-semibold text-white">Design Validation</h3>
          </div>
          <div className="space-y-3">
            {designValidation.issues.map((issue, idx) => {
              // Find fix suggestions for this issue
              const fixSuggestion = (designValidation as any).fix_suggestions?.find(
                (fix: any) => fix.issue?.type === issue.type && fix.issue?.message === issue.message
              );
              
              return (
                <div key={idx} className={`p-3 rounded ${
                  issue.severity === "error" ? "bg-red-900/20 border border-red-500/50" : "bg-yellow-900/20 border border-yellow-500/50"
                }`}>
                  <div className="flex items-start justify-between mb-2">
                    <div className="text-sm text-white">{issue.message}</div>
                    {issue.severity === "error" && (
                      <Badge variant="destructive" className="ml-2">Error</Badge>
                    )}
                  </div>
                  
                  {fixSuggestion && fixSuggestion.suggested_parts && fixSuggestion.suggested_parts.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-zinc-700">
                      <div className="flex items-center gap-2 mb-2">
                        <Wrench className="w-4 h-4 text-neon-teal" />
                        <span className="text-xs font-medium text-neon-teal">Suggested Fixes:</span>
                      </div>
                      <div className="space-y-2">
                        {fixSuggestion.suggested_parts.slice(0, 3).map((suggestedPart: any, partIdx: number) => {
                          const partObj = convertPartDataToPartObject(suggestedPart);
                          return (
                            <div key={partIdx} className="flex items-center justify-between p-2 bg-dark-bg rounded text-xs">
                              <div className="flex-1">
                                <div className="text-white font-medium">{suggestedPart.name || suggestedPart.mfr_part_number}</div>
                                <div className="text-neutral-blue">{suggestedPart.manufacturer} - {suggestedPart.mfr_part_number}</div>
                                {suggestedPart.cost_estimate?.value && (
                                  <div className="text-neon-teal">${suggestedPart.cost_estimate.value.toFixed(2)}</div>
                                )}
                              </div>
                              {onPartAdd && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="ml-2 h-7 px-2 text-xs"
                                  onClick={() => onPartAdd(partObj)}
                                >
                                  <Plus className="w-3 h-3 mr-1" />
                                  Add
                                </Button>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
            
            {/* Warnings with fix suggestions */}
            {designValidation.warnings.map((warning, idx) => {
              // Normalize warning to object format
              const warningObj = typeof warning === "string" ? { message: warning } : warning;
              const warningText = typeof warning === "string" ? warning : warning.message;
              
              // Check for fix suggestions related to this warning
              const relatedFix = (designValidation as any).fix_suggestions?.find(
                (fix: any) => warningText.toLowerCase().includes(fix.fix_type?.toLowerCase() || "")
              );
              
              return (
                <div key={idx} className="p-3 bg-yellow-900/20 border border-yellow-500/50 rounded">
                  <div className="text-sm text-yellow-400 mb-2">{warningText}</div>
                  
                  {relatedFix && relatedFix.suggested_parts && relatedFix.suggested_parts.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-yellow-500/30">
                      <div className="flex items-center gap-2 mb-2">
                        <Wrench className="w-4 h-4 text-yellow-400" />
                        <span className="text-xs font-medium text-yellow-400">Suggested:</span>
                      </div>
                      <div className="space-y-1">
                        {relatedFix.suggested_parts.slice(0, 2).map((suggestedPart: any, partIdx: number) => {
                          const partObj = convertPartDataToPartObject(suggestedPart);
                          return (
                            <div key={partIdx} className="flex items-center justify-between p-1.5 bg-dark-bg rounded text-xs">
                              <div className="flex-1 text-white">
                                {suggestedPart.name || suggestedPart.mfr_part_number}
                              </div>
                              {onPartAdd && (
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="ml-2 h-6 px-2 text-xs"
                                  onClick={() => onPartAdd(partObj)}
                                >
                                  <Plus className="w-3 h-3" />
                                </Button>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Power Breakdown */}
      {powerAnalysis && Object.keys(powerAnalysis.power_by_rail).length > 0 && (
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-5 h-5 text-neon-teal" />
            <h3 className="text-lg font-semibold text-white">Power by Rail</h3>
          </div>
          <div className="space-y-2">
            {Object.entries(powerAnalysis.power_by_rail).map(([rail, power]) => (
              <div key={rail} className="flex items-center justify-between p-2 bg-dark-bg rounded">
                <span className="text-sm text-white">{rail}</span>
                <span className="text-sm font-semibold text-neon-teal">{power.toFixed(2)}W</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

