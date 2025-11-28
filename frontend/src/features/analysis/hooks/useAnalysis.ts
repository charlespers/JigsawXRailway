/**
 * useAnalysis Hook
 * Handles design analysis operations
 */

import { useState, useCallback, useEffect } from "react";
import { useDesignStore } from "../../design-generation/store/designStore";
import {
  analyzeCost,
  analyzeSupplyChain,
  calculatePower,
  validateDesign,
  analyzeManufacturingReadiness,
  analyzeSignalIntegrity,
  analyzeThermal,
} from "../services/analysisApi";

interface AnalysisResults {
  cost: any;
  supplyChain: any;
  power: any;
  validation: any;
  manufacturing: any;
  signalIntegrity: any;
  thermal: any;
}

function useAnalysis() {
  const { parts, connections } = useDesignStore();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<AnalysisResults>({
    cost: null,
    supplyChain: null,
    power: null,
    validation: null,
    manufacturing: null,
    signalIntegrity: null,
    thermal: null,
  });

  const runAllAnalyses = useCallback(async () => {
    if (parts.length === 0) return;

    setLoading(true);
    const bomItems = parts.map((part) => ({
      part_data: part,
      quantity: part.quantity || 1,
    }));

    try {
      const [
        cost,
        supplyChain,
        power,
        validation,
        manufacturing,
        signalIntegrity,
        thermal,
      ] = await Promise.allSettled([
        analyzeCost(bomItems),
        analyzeSupplyChain(bomItems),
        calculatePower(bomItems),
        validateDesign(bomItems, connections),
        analyzeManufacturingReadiness(bomItems, connections),
        analyzeSignalIntegrity(bomItems, connections),
        analyzeThermal(bomItems),
      ]);

      setResults({
        cost: cost.status === "fulfilled" ? cost.value : null,
        supplyChain:
          supplyChain.status === "fulfilled" ? supplyChain.value : null,
        power: power.status === "fulfilled" ? power.value : null,
        validation:
          validation.status === "fulfilled" ? validation.value : null,
        manufacturing:
          manufacturing.status === "fulfilled" ? manufacturing.value : null,
        signalIntegrity:
          signalIntegrity.status === "fulfilled" ? signalIntegrity.value : null,
        thermal: thermal.status === "fulfilled" ? thermal.value : null,
      });
    } catch (error) {
      console.error("Analysis failed:", error);
    } finally {
      setLoading(false);
    }
  }, [parts, connections]);

  return {
    loading,
    results,
    runAllAnalyses,
  };
}

export default useAnalysis;
export { useAnalysis };
