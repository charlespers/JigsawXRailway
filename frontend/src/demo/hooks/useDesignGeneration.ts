/**
 * Custom hook for design generation
 * Extracts design generation logic from JigsawDemo
 */

import { useCallback, useRef } from 'react';
import { useDesignStore } from '../store/designStore';
import { componentAnalysisApi } from '../services';
import { useToast } from '../components/Toast';
import type { PartObject } from '../services/types';

export function useDesignGeneration() {
  const {
    setParts,
    setConnections,
    setDesignHealth,
    setIsAnalyzing,
    setError,
    setSessionId,
    setQuery,
    setProvider,
    query,
    provider,
    sessionId,
    parts,
    saveToHistory,
  } = useDesignStore();
  
  const { showToast } = useToast();
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleQuerySent = useCallback(async (
    newQuery: string,
    newProvider: 'openai' | 'xai'
  ) => {
    // Cancel any ongoing analysis
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Update state
    setQuery(newQuery);
    setProvider(newProvider);
    setIsAnalyzing(true);
    setError(null);

    // Reset design if it's a completely new query
    const isNewQuery = newQuery.trim() !== query.trim();
    if (isNewQuery && parts.length > 0) {
      setParts([]);
      setConnections([]);
      setDesignHealth(null);
    }

    // Get or create session ID
    let currentSessionId = sessionId;
    if (!currentSessionId || isNewQuery) {
      currentSessionId = `session_${Date.now()}`;
      setSessionId(currentSessionId);
    }

    try {
      // Handle updates from SSE stream
      const handleUpdate = (event: any) => {
        if (abortController.signal.aborted) return;

        switch (event.type) {
          case 'selection':
            if (event.partData) {
              const part = event.partData as PartObject;
              // Check for duplicates before adding
              const exists = parts.some(p => 
                p.mpn === part.mpn && 
                p.manufacturer === part.manufacturer
              );
              
              if (!exists) {
                setParts([...parts, part]);
              } else {
                showToast(`${part.mpn} is already in the BOM`, "warning", 2000);
              }
            }
            break;

          case 'complete':
            setIsAnalyzing(false);
            saveToHistory();
            showToast("Design generation complete!", "success", 3000);
            break;

          case 'error':
            setError(event.message || 'An error occurred');
            setIsAnalyzing(false);
            showToast(event.message || 'An error occurred', "error", 5000);
            break;

          case 'reasoning':
            // Reasoning events are handled by the UI component
            break;
        }
      };

      // Start analysis
      await componentAnalysisApi.startAnalysis(
        newQuery,
        newProvider,
        handleUpdate,
        abortController.signal
      );

    } catch (error: any) {
      if (error.name === 'AbortError') {
        // User cancelled, don't show error
        return;
      }
      
      const errorMessage = error.message || 'Failed to generate design';
      setError(errorMessage);
      setIsAnalyzing(false);
      showToast(errorMessage, "error", 5000);
    } finally {
      abortControllerRef.current = null;
    }
  }, [
    query,
    provider,
    sessionId,
    parts,
    setParts,
    setConnections,
    setDesignHealth,
    setIsAnalyzing,
    setError,
    setSessionId,
    setQuery,
    setProvider,
    saveToHistory,
    showToast,
  ]);

  const cancelAnalysis = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsAnalyzing(false);
      showToast("Analysis cancelled", "info", 2000);
    }
  }, [setIsAnalyzing, showToast]);

  return {
    handleQuerySent,
    cancelAnalysis,
  };
}

