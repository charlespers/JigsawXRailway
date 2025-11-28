/**
 * useBOMManagement Hook
 * Handles BOM operations (add, remove, update parts)
 */

import { useCallback } from "react";
import { useDesignStore } from "../../design-generation/store/designStore";
import type { PartObject } from "../../shared/services/types";

function useBOMManagement() {
  const { parts, setParts } = useDesignStore();

  const addPartToBOM = useCallback(
    (part: PartObject) => {
      setParts((prev) => {
        // Check for duplicates
        const existingIndex = prev.findIndex(
          (p) =>
            p.componentId === part.componentId &&
            p.mpn === part.mpn &&
            p.manufacturer === part.manufacturer
        );

        if (existingIndex >= 0) {
          // Increment quantity
          return prev.map((p, idx) =>
            idx === existingIndex
              ? { ...p, quantity: (p.quantity || 1) + 1 }
              : p
          );
        }

        // Add new part
        return [...prev, { ...part, quantity: part.quantity || 1 }];
      });
    },
    [setParts]
  );

  const removePartFromBOM = useCallback(
    (componentId: string) => {
      setParts((prev) => prev.filter((p) => p.componentId !== componentId));
    },
    [setParts]
  );

  const updatePartInBOM = useCallback(
    (componentId: string, updates: Partial<PartObject>) => {
      setParts((prev) =>
        prev.map((p) =>
          p.componentId === componentId ? { ...p, ...updates } : p
        )
      );
    },
    [setParts]
  );

  const bulkUpdateParts = useCallback(
    (updates: Array<{ componentId: string; updates: Partial<PartObject> }>) => {
      setParts((prev) => {
        const updateMap = new Map(
          updates.map((u) => [u.componentId, u.updates])
        );
        return prev.map((p) =>
          updateMap.has(p.componentId)
            ? { ...p, ...updateMap.get(p.componentId) }
            : p
        );
      });
    },
    [setParts]
  );

  return {
    addPartToBOM,
    removePartFromBOM,
    updatePartInBOM,
    bulkUpdateParts,
  };
}

export default useBOMManagement;
export { useBOMManagement };
