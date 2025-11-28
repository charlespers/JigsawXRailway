/**
 * useDesignGeneration Hook
 * Handles design generation workflow
 */

import { useState, useCallback } from "react";
import { useDesignStore } from "../../design-generation/store/designStore";
import { componentAnalysisApi } from "../../shared/services/componentAnalysisApi";
import type { PartObject } from "../../shared/services/types";

function useDesignGeneration() {
  const { setParts, setConnections, setIsAnalyzing, setError } = useDesignStore();
  const [isGenerating, setIsGenerating] = useState(false);

  const handleQuerySent = useCallback(
    async (
      query: string,
      provider: "xai" = "xai",
      onUpdate?: (update: any) => void
    ) => {
      setIsGenerating(true);
      setIsAnalyzing(true);
      setError(null);

      try {
        const parts: PartObject[] = [];
        const connections: any[] = [];

        await componentAnalysisApi.startAnalysis(
          query,
          provider,
          (update: any) => {
            onUpdate?.(update);

            if (update.type === "selection" && update.partData) {
              const part: PartObject = {
                componentId: update.componentId || `part_${parts.length}`,
                mpn: update.partData.mfr_part_number || update.partData.id || "",
                manufacturer: update.partData.manufacturer || "",
                description: update.partData.description || "",
                price: update.partData.cost_estimate?.value || 0,
                currency: update.partData.cost_estimate?.currency || "USD",
                voltage: update.partData.supply_voltage_range
                  ? `${update.partData.supply_voltage_range.min || ""}V ~ ${update.partData.supply_voltage_range.max || ""}V`
                  : undefined,
                package: update.partData.package || "",
                interfaces: update.partData.interface_type || [],
                datasheet: update.partData.datasheet_url || "",
                quantity: 1,
                category: update.partData.category,
                footprint: update.partData.footprint,
                lifecycle_status: update.partData.lifecycle_status,
                availability_status: update.partData.availability_status,
              };
              parts.push(part);
            }

            if (update.type === "complete") {
              setParts([...parts]);
              setIsAnalyzing(false);
            }
          }
        );
      } catch (error: any) {
        setError(error.message || "Design generation failed");
        setIsAnalyzing(false);
      } finally {
        setIsGenerating(false);
      }
    },
    [setParts, setConnections, setIsAnalyzing, setError]
  );

  const cancelAnalysis = useCallback(() => {
    setIsAnalyzing(false);
    setIsGenerating(false);
  }, [setIsAnalyzing]);

  return {
    handleQuerySent,
    cancelAnalysis,
    isGenerating,
  };
}

export default useDesignGeneration;
export { useDesignGeneration };
