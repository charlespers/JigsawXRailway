/**
 * Custom hook for design analysis
 * Handles running various analyses on the design
 */

import { useState, useCallback } from 'react';
import { useDesignStore } from '../store/designStore';
import {
  analyzeCost,
  analyzeSupplyChain,
  calculatePower,
  validateDesign,
  analyzeManufacturingReadiness,
  analyzeSignalIntegrity,
  analyzeThermal,
  type CostAnalysis,
  type SupplyChainAnalysis,
  type PowerAnalysis,
  type DesignValidation,
  type ManufacturingReadiness,
  type SignalIntegrityAnalysis,
  type ThermalAnalysis,
} from '../services/analysisApi';
import { useToast } from '../components/Toast';

export interface AnalysisResults {
  cost: CostAnalysis | null;
  supplyChain: SupplyChainAnalysis | null;
  power: PowerAnalysis | null;
  validation: DesignValidation | null;
  manufacturing: ManufacturingReadiness | null;
  signalIntegrity: SignalIntegrityAnalysis | null;
  thermal: ThermalAnalysis | null;
}

export function useAnalysis() {
  const { parts, connections } = useDesignStore();
  const { showToast } = useToast();
  
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

  const runAnalysis = useCallback(async (
    analysisType: keyof AnalysisResults,
    options?: any
  ) => {
    if (parts.length === 0) {
      showToast("No parts in design to analyze", "warning", 3000);
      return;
    }

    setLoading(true);
    
    try {
      const bomItems = parts.map(part => ({
        part_data: part,
        quantity: part.quantity || 1,
      }));

      let result: any = null;

      switch (analysisType) {
        case 'cost':
          result = await analyzeCost(bomItems);
          break;
        case 'supplyChain':
          result = await analyzeSupplyChain(bomItems);
          break;
        case 'power':
          result = await calculatePower(bomItems, options);
          break;
        case 'validation':
          result = await validateDesign(bomItems, connections);
          break;
        case 'manufacturing':
          result = await analyzeManufacturingReadiness(bomItems, connections);
          break;
        case 'signalIntegrity':
          result = await analyzeSignalIntegrity(bomItems, connections, options);
          break;
        case 'thermal':
          result = await analyzeThermal(bomItems);
          break;
        default:
          throw new Error(`Unknown analysis type: ${analysisType}`);
      }

      setResults(prev => ({
        ...prev,
        [analysisType]: result,
      }));

      showToast(`${analysisType} analysis complete`, "success", 2000);
      return result;
    } catch (error: any) {
      const errorMessage = error.message || `Failed to run ${analysisType} analysis`;
      showToast(errorMessage, "error", 5000);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [parts, connections, showToast]);

  const runAllAnalyses = useCallback(async () => {
    if (parts.length === 0) {
      showToast("No parts in design to analyze", "warning", 3000);
      return;
    }

    setLoading(true);
    
    try {
      const bomItems = parts.map(part => ({
        part_data: part,
        quantity: part.quantity || 1,
      }));

      // Run all analyses in parallel
      const [
        costResult,
        supplyChainResult,
        powerResult,
        validationResult,
        manufacturingResult,
        signalIntegrityResult,
        thermalResult,
      ] = await Promise.allSettled([
        analyzeCost(bomItems).catch(() => null),
        analyzeSupplyChain(bomItems).catch(() => null),
        calculatePower(bomItems).catch(() => null),
        validateDesign(bomItems, connections).catch(() => null),
        analyzeManufacturingReadiness(bomItems, connections).catch(() => null),
        analyzeSignalIntegrity(bomItems, connections).catch(() => null),
        analyzeThermal(bomItems).catch(() => null),
      ]);

      setResults({
        cost: costResult.status === 'fulfilled' ? costResult.value : null,
        supplyChain: supplyChainResult.status === 'fulfilled' ? supplyChainResult.value : null,
        power: powerResult.status === 'fulfilled' ? powerResult.value : null,
        validation: validationResult.status === 'fulfilled' ? validationResult.value : null,
        manufacturing: manufacturingResult.status === 'fulfilled' ? manufacturingResult.value : null,
        signalIntegrity: signalIntegrityResult.status === 'fulfilled' ? signalIntegrityResult.value : null,
        thermal: thermalResult.status === 'fulfilled' ? thermalResult.value : null,
      });

      showToast("All analyses complete", "success", 3000);
    } catch (error: any) {
      showToast("Failed to run some analyses", "error", 5000);
    } finally {
      setLoading(false);
    }
  }, [parts, connections, showToast]);

  const clearResults = useCallback(() => {
    setResults({
      cost: null,
      supplyChain: null,
      power: null,
      validation: null,
      manufacturing: null,
      signalIntegrity: null,
      thermal: null,
    });
  }, []);

  return {
    loading,
    results,
    runAnalysis,
    runAllAnalyses,
    clearResults,
  };
}

