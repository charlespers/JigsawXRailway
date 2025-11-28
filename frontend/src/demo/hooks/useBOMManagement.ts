/**
 * Custom hook for BOM management
 * Handles BOM operations like adding, removing, updating parts
 */

import { useCallback } from 'react';
import { useDesignStore } from '../store/designStore';
import { useToast } from '../components/Toast';
import type { PartObject } from '../services/types';

export function useBOMManagement() {
  const {
    parts,
    setParts,
    addPart,
    removePart,
    updatePart,
    saveToHistory,
  } = useDesignStore();
  
  const { showToast } = useToast();

  const addPartToBOM = useCallback((part: PartObject) => {
    // Check for duplicates
    const exists = parts.some(p => 
      p.mpn === part.mpn && 
      p.manufacturer === part.manufacturer
    );
    
    if (exists) {
      showToast(`${part.mpn} is already in the BOM`, "warning", 2000);
      return false;
    }
    
    addPart(part);
    saveToHistory();
    showToast(`Added ${part.mpn} to BOM`, "success", 2000);
    return true;
  }, [parts, addPart, saveToHistory, showToast]);

  const removePartFromBOM = useCallback((componentId: string) => {
    const part = parts.find(p => p.componentId === componentId);
    if (part) {
      removePart(componentId);
      saveToHistory();
      showToast(`Removed ${part.mpn} from BOM`, "info", 2000);
      return true;
    }
    return false;
  }, [parts, removePart, saveToHistory, showToast]);

  const updatePartInBOM = useCallback((
    componentId: string,
    updates: Partial<PartObject>
  ) => {
    const part = parts.find(p => p.componentId === componentId);
    if (part) {
      updatePart(componentId, updates);
      saveToHistory();
      showToast(`Updated ${part.mpn}`, "success", 2000);
      return true;
    }
    return false;
  }, [parts, updatePart, saveToHistory, showToast]);

  const bulkUpdateParts = useCallback((
    updates: Array<{ componentId: string; updates: Partial<PartObject> }>
  ) => {
    updates.forEach(({ componentId, updates: partUpdates }) => {
      updatePart(componentId, partUpdates);
    });
    saveToHistory();
    showToast(`Updated ${updates.length} part(s)`, "success", 2000);
  }, [updatePart, saveToHistory, showToast]);

  const clearBOM = useCallback(() => {
    setParts([]);
    saveToHistory();
    showToast("BOM cleared", "info", 2000);
  }, [setParts, saveToHistory, showToast]);

  return {
    parts,
    addPartToBOM,
    removePartFromBOM,
    updatePartInBOM,
    bulkUpdateParts,
    clearBOM,
  };
}

