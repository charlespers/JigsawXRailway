/**
 * Jigsaw PCB Design Demo Component
 * 
 * Standalone component for integrating the Jigsaw demo into your website.
 * 
 * Usage:
 * ```tsx
 * import JigsawDemo from './JigsawDemo';
 * 
 * <JigsawDemo 
 *   backendUrl="http://localhost:3001"
 *   initialQuery="WiFi temperature sensor board"
 * />
 * ```
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { motion } from "motion/react";
import ComponentGraph from "./components/ComponentGraph";
import PCBViewer from "./components/PCBViewer";
import PartsList from "./components/PartsList";
import DesignChat from "./components/DesignChat";
import SettingsPanel from "./components/SettingsPanel";
import BOMInsights from "./components/BOMInsights";
import ErrorBoundary from "./components/ErrorBoundary";
import ErrorDisplay from "./components/ErrorDisplay";
import DesignHealthScore from "./components/DesignHealthScore";
import DesignComparison from "./components/DesignComparison";
import DesignTemplates from "./components/DesignTemplates";
import DesignValidationPanel from "./components/validation/DesignValidationPanel";
import { useToast } from "./components/Toast";
import type { PartObject } from "./services/types";
import { componentAnalysisApi } from "./services";
import configService from "./services/config";
import { normalizePartObject, normalizeQuantity } from "./utils/partNormalizer";

export interface JigsawDemoProps {
  /** Backend API URL (optional, defaults to config service) */
  backendUrl?: string;
  /** Initial query to start analysis with */
  initialQuery?: string;
  /** Custom CSS class name */
  className?: string;
  /** Height of the demo container */
  height?: string;
}

export default function JigsawDemo({
  backendUrl,
  initialQuery = "",
  className = "",
  height = "100vh",
}: JigsawDemoProps) {
  // Configure API services
  useEffect(() => {
    const url = backendUrl || configService.getBackendUrl();
    componentAnalysisApi.updateConfig({ baseUrl: url });
    if (backendUrl) {
      configService.updateConfig({ backendUrl: url });
    }
  }, [backendUrl]);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [analysisQuery, setAnalysisQuery] = useState<string>(initialQuery);
  const [provider, setProvider] = useState<"xai">("xai");
  const [parts, setParts] = useState<PartObject[]>([]);
  const [activeTab, setActiveTab] = useState<"design" | "bom" | "analysis" | "templates">("design");
  const [previousDesign, setPreviousDesign] = useState<PartObject[] | null>(null);
  const [connections] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [designHealth, setDesignHealth] = useState<{
    healthScore: number;
    healthLevel: string;
    healthBreakdown?: any;
  } | null>(null);
  const { showToast, ToastComponent } = useToast();
  const [designHistory, setDesignHistory] = useState<PartObject[][]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [selectedComponents, setSelectedComponents] = useState<
    Map<
      string,
      {
        id: string;
        label: string;
        position: { x: number; y: number };
        color?: string;
        size?: { w: number; h: number };
        partData?: PartObject;
      }
    >
  >(new Map());

  // Track previous query to detect new queries
  const previousQueryRef = useRef<string>("");
  const highestHierarchyRef = useRef<number>(-1);
  
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf("MAC") >= 0;
      const ctrlKey = isMac ? e.metaKey : e.ctrlKey;
      
      // Ctrl/Cmd + S: Save design
      if (ctrlKey && e.key === "s") {
        e.preventDefault();
        handleSaveDesign();
      }
      
      // Ctrl/Cmd + Z: Undo
      if (ctrlKey && e.key === "z" && !e.shiftKey) {
        e.preventDefault();
        handleUndo();
      }
      
      // Ctrl/Cmd + Shift + Z: Redo
      if (ctrlKey && e.key === "z" && e.shiftKey) {
        e.preventDefault();
        handleRedo();
      }
      
      // Ctrl/Cmd + F: Focus search (if chat input exists)
      if (ctrlKey && e.key === "f") {
        e.preventDefault();
        // Focus chat input if available
        const chatInput = document.querySelector('textarea[placeholder*="query"], input[placeholder*="query"]') as HTMLElement;
        if (chatInput) {
          chatInput.focus();
        }
      }
      
      // Esc: Dismiss modals/panels
      if (e.key === "Escape") {
        setError(null);
      }
    };
    
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [parts]);
  
  // Save design to history for undo/redo
  const saveToHistory = useCallback((currentParts: PartObject[]) => {
    setDesignHistory((prev) => {
      const newHistory = prev.slice(0, historyIndex + 1);
      newHistory.push([...currentParts]);
      return newHistory.slice(-50); // Keep last 50 states
    });
    setHistoryIndex((prev) => Math.min(prev + 1, 49));
  }, [historyIndex]);
  
  // Undo handler
  const handleUndo = useCallback(() => {
    if (historyIndex > 0) {
      const previousParts = designHistory[historyIndex - 1];
      setParts(previousParts);
      setHistoryIndex((prev) => prev - 1);
      showToast("Design undone", "info", 2000);
    }
  }, [historyIndex, designHistory, showToast]);
  
  // Redo handler
  const handleRedo = useCallback(() => {
    if (historyIndex < designHistory.length - 1) {
      const nextParts = designHistory[historyIndex + 1];
      setParts(nextParts);
      setHistoryIndex((prev) => prev + 1);
      showToast("Design redone", "info", 2000);
    }
  }, [historyIndex, designHistory, showToast]);
  
  // Save design handler
  const handleSaveDesign = useCallback(() => {
    // CRITICAL: Ensure all parts have componentId before export
    const validatedParts = parts.map((part, index) => ({
      ...part,
      componentId: part.componentId || `exported_${index}`,  // Ensure componentId exists
    }));
    
    const designData = {
      parts: validatedParts,  // Export with componentId preserved
      connections,
      query: analysisQuery,
      timestamp: new Date().toISOString(),
      version: "1.0",  // Version for future compatibility
    };
    
    const blob = new Blob([JSON.stringify(designData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `design_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast(`Design exported successfully: ${validatedParts.length} part(s)`, "success", 2000);
  }, [parts, connections, analysisQuery, showToast]);
  
  // Load design handler
  const handleLoadDesign = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const designData = JSON.parse(e.target?.result as string);
        if (designData.parts && Array.isArray(designData.parts)) {
          // CRITICAL: Ensure all parts have componentId
          // CRITICAL: Normalize all imported parts to prevent runtime errors
          const validatedParts = designData.parts.map((part: any, index: number) => 
            normalizePartObject({
              ...part,
              componentId: part.componentId || `imported_${index}`,  // Ensure componentId exists
            })
          );
          
          // CRITICAL: Update both parts array AND selectedComponents Map
          // This ensures parts are displayed in both PartsList and PCBViewer
          setParts(validatedParts);
          
          // Reconstruct selectedComponents Map from loaded parts
          const newSelectedComponents = new Map();
          validatedParts.forEach((part: PartObject, index: number) => {
            // componentId should be preserved from export
            const componentId = part.componentId || `imported_${index}`;
            const partMpn = part.mpn || `part_${index}`;
            
            // Calculate position for visualization
            const existingComponents = Array.from(newSelectedComponents.values()).map((c) => ({
              id: c.id,
              position: c.position,
              size: c.size,
            }));
            
            const organizedPosition = calculateComponentPosition(
              componentId,
              existingComponents,
              index
            );
            
            newSelectedComponents.set(componentId, {
              id: componentId,
              label: partMpn.split("-")[0] || componentId,
              position: organizedPosition,
              partData: part,
            });
          });
          
          setSelectedComponents(newSelectedComponents);
          
          if (designData.query) {
            setAnalysisQuery(designData.query);
          }
          
          // Reset hierarchy tracking for loaded design
          highestHierarchyRef.current = validatedParts.length - 1;
          
          saveToHistory(validatedParts);
          showToast(`Design loaded successfully: ${validatedParts.length} part(s)`, "success", 3000);
        } else {
          showToast("Invalid design file format: missing parts array", "error", 3000);
        }
      } catch (error) {
        console.error("Failed to load design:", error);
        showToast(`Failed to load design file: ${error instanceof Error ? error.message : 'Unknown error'}`, "error", 3000);
      }
    };
    reader.readAsText(file);
  }, [showToast, saveToHistory]);

  // Update query when initialQuery changes and auto-start analysis
  useEffect(() => {
    if (
      initialQuery &&
      initialQuery.trim() &&
      initialQuery !== previousQueryRef.current
    ) {
      setParts([]);
      setSelectedComponents(new Map());
      previousQueryRef.current = initialQuery;
      setAnalysisQuery(initialQuery);
      setIsAnalyzing(true);
    }
  }, [initialQuery]);

  // Handle query sent from chat - start analysis
  const handleQuerySent = (query: string, selectedProvider: "xai" = "xai") => {
    // Get or create session ID
    let currentSessionId = sessionId;
    if (!currentSessionId) {
      const storedSessionId = localStorage.getItem("jigsaw_session_id");
      if (storedSessionId) {
        currentSessionId = storedSessionId;
        setSessionId(storedSessionId);
      }
    }
    
    // Only reset if this is clearly a new design request (not a follow-up question)
    // Check if query looks like a new design vs. a question/refinement
    const isNewDesign = !query.toLowerCase().includes("?") && 
                        !query.toLowerCase().includes("what") &&
                        !query.toLowerCase().includes("how") &&
                        !query.toLowerCase().includes("change") &&
                        !query.toLowerCase().includes("replace") &&
                        (previousQueryRef.current === "" || 
                         (previousQueryRef.current !== query && parts.length === 0));
    
    if (isNewDesign) {
      setParts([]);
      setSelectedComponents(new Map());
      highestHierarchyRef.current = -1;
      // Clear session for new design
      localStorage.removeItem("jigsaw_session_id");
      setSessionId(null);
    }
    
    previousQueryRef.current = query;
    setProvider(selectedProvider);
    setAnalysisQuery(query);
    setIsAnalyzing(true);
  };

  // Handle query killed/reset - clear everything
  const handleQueryKilled = () => {
    setIsAnalyzing(false);
    setParts([]);
    setSelectedComponents(new Map());
    setAnalysisQuery("");
    highestHierarchyRef.current = -1;
    previousQueryRef.current = "";
  };

  // Layout system for organized PCB placement (supports demo's component IDs)
  const calculateComponentPosition = (
    componentId: string,
    existingComponents: Array<{
      id: string;
      position: { x: number; y: number };
      size?: { w: number; h: number };
    }>,
    _hierarchyLevel: number
  ): { x: number; y: number } => {
    const componentTypes: Record<string, { row: number; col: number }> = {
      // Main components (demo naming)
      anchor: { row: 1, col: 2 }, // Anchor/MCU component
      mcu: { row: 1, col: 2 },
      power: { row: 0, col: 2 },
      connector: { row: 0, col: 1 },
      sensor: { row: 1, col: 0 },
      sensors: { row: 1, col: 0 },
      memory: { row: 1, col: 4 },
      antenna: { row: 0, col: 3 },
      passives: { row: 2, col: 2 },
      // New component types
      test_point: { row: 3, col: 0 }, // Test points at bottom
      fiducial: { row: 0, col: 0 }, // Fiducials at corners
    };

    const viewportWidth =
      typeof window !== "undefined" ? window.innerWidth : 1920;
    const viewportHeight =
      typeof window !== "undefined" ? window.innerHeight : 1080;
    const gridSpacing = Math.max(60, Math.min(100, viewportWidth * 0.08));
    const startX = Math.max(150, viewportWidth * 0.15);
    const startY = Math.max(100, viewportHeight * 0.15);

    const idLower = componentId.toLowerCase();
    
    // Check for test points and fiducials first
    if (idLower.includes("test_point") || idLower.startsWith("tp")) {
      // Place test points along bottom edge
      const tpIndex = existingComponents.filter(c => 
        c.id.toLowerCase().includes("test_point") || c.id.toLowerCase().startsWith("tp")
      ).length;
      return {
        x: startX + (tpIndex % 6) * (gridSpacing * 0.8),
        y: startY + 4 * gridSpacing,
      };
    }
    
    if (idLower.includes("fiducial") || idLower.startsWith("fid")) {
      // Place fiducials at corners
      const fidIndex = existingComponents.filter(c => 
        c.id.toLowerCase().includes("fiducial") || c.id.toLowerCase().startsWith("fid")
      ).length;
      const corners = [
        { x: startX - gridSpacing * 0.5, y: startY - gridSpacing * 0.5 }, // Top-left
        { x: startX + 5 * gridSpacing, y: startY - gridSpacing * 0.5 }, // Top-right
        { x: startX - gridSpacing * 0.5, y: startY + 3 * gridSpacing }, // Bottom-left
      ];
      return corners[fidIndex] || corners[0];
    }
    
    // Check for intermediaries
    if (idLower.includes("intermediary")) {
      // Place intermediaries near power components
      const intermediaryIndex = existingComponents.filter(c => 
        c.id.toLowerCase().includes("intermediary")
      ).length;
      return {
        x: startX + 1 * gridSpacing + (intermediaryIndex * gridSpacing * 0.5),
        y: startY + 0.5 * gridSpacing,
      };
    }
    
    // Check exact match first
    const layout = componentTypes[idLower];
    if (layout) {
      return {
        x: startX + layout.col * gridSpacing,
        y: startY + layout.row * gridSpacing,
      };
    }
    
    // Check partial matches
    for (const [key, pos] of Object.entries(componentTypes)) {
      if (idLower.includes(key)) {
        return {
          x: startX + pos.col * gridSpacing,
          y: startY + pos.row * gridSpacing,
        };
      }
    }

    // Default: place in grid based on existing count
    const existingCount = existingComponents.length;
    const colsPerRow = 4;
    const row = Math.floor(existingCount / colsPerRow);
    const col = existingCount % colsPerRow;

    return {
      x: startX + col * gridSpacing,
      y: startY + (row + 3) * gridSpacing,
    };
  };

  const handleComponentSelected = (
    componentId: string,
    partData: any,
    _position?: { x: number; y: number },
    hierarchyOffset?: number
  ) => {
    // CRITICAL: Normalize part data to ensure price and quantity are always numbers
    // This prevents "dict * float" errors
    const normalizedPart = normalizePartObject({
      ...partData,
      componentId: partData.componentId || componentId,  // Use partData.componentId if present, fallback to parameter
    });
    
    // CRITICAL: Track parts by componentId to handle cases where same part is used in different components
    // Enhanced duplicate check: componentId + mpn + manufacturer
    setParts((prev) => {
      // Check if this exact component-part combination already exists
      const existingIndex = prev.findIndex((p) => {
        return p.componentId === normalizedPart.componentId && 
               p.mpn === normalizedPart.mpn &&
               p.manufacturer === normalizedPart.manufacturer;
      });
      
      if (existingIndex >= 0) {
        // Duplicate detected - increment quantity and show info toast
        showToast(`Part ${normalizedPart.mpn} already exists, incrementing quantity`, "info", 2000);
        return prev.map((p, idx) => {
          if (idx === existingIndex) {
            return { ...p, quantity: normalizeQuantity(p.quantity) + 1 };
          }
          return p;
        });
      }
      
      // New part selection - add with normalized data
      return [...prev, normalizedPart];
    });

    setSelectedComponents((prev) => {
      const newMap = new Map(prev);
      const existingComponents = Array.from(prev.values()).map((c) => ({
        id: c.id,
        position: c.position,
        size: c.size,
      }));

      const organizedPosition = calculateComponentPosition(
        componentId,
        existingComponents,
        hierarchyOffset || 0
      );

      newMap.set(componentId, {
        id: componentId,
        label: partData.mpn.split("-")[0] || componentId,
        position: organizedPosition,
        partData,
      });
      return newMap;
    });
  };

  const handleAnalysisComplete = useCallback(() => {
    setIsAnalyzing(false);
    setIsCompleted(true);
    // Show success message with part count - use current parts state
    // Use setTimeout to ensure parts state is updated after all selection events
    setTimeout(() => {
      const partCount = parts.length;
      if (partCount > 0) {
        showToast(`✓ Design complete! ${partCount} part(s) selected.`, "success", 4000);
      } else {
        showToast("Analysis complete. No parts were selected.", "info", 3000);
      }
    }, 500); // Delay to ensure all selection events have been processed
  }, [parts.length, showToast]);

  // Load settings from localStorage
  useEffect(() => {
    const savedBackendUrl = localStorage.getItem("demo_backend_url");
    const savedProvider = localStorage.getItem("demo_provider");
    if (savedBackendUrl) {
      componentAnalysisApi.updateConfig({ baseUrl: savedBackendUrl });
    }
    // Only use saved provider if it's valid, otherwise default to "xai"
    if (savedProvider === "xai") {
      setProvider(savedProvider);
    } else {
      // Ensure default is "xai" if localStorage has invalid value
      setProvider("xai");
      localStorage.setItem("demo_provider", "xai");
    }
  }, []);

  return (
    <ErrorBoundary>
      <div
        className={`h-screen bg-zinc-950 text-white flex flex-col overflow-hidden ${className}`}
        style={{ height }}
      >
        {error && (
          <div className="p-4 border-b border-red-500/50 bg-red-500/10">
            <ErrorDisplay
              error={error}
              onRetry={() => {
                setError(null);
                if (analysisQuery) {
                  setIsAnalyzing(true);
                }
              }}
              onDismiss={() => setError(null)}
              variant="error"
            />
          </div>
        )}
        <SettingsPanel
        backendUrl={backendUrl || configService.getBackendUrl()}
        defaultProvider={provider}
        onBackendUrlChange={(url) => {
          componentAnalysisApi.updateConfig({ baseUrl: url });
        }}
        onProviderChange={(p) => setProvider(p)}
      />
      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Left Panel - Component Graph */}
        <motion.div
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="w-[20vw] min-w-[280px] max-w-[400px] border-r border-zinc-800 bg-zinc-900/30 flex flex-col overflow-hidden h-full"
        >
          <div className="flex-1 overflow-y-auto min-h-0">
            <ComponentGraph
              onComponentSelected={handleComponentSelected}
              analysisQuery={analysisQuery}
              provider={provider}
              isAnalyzing={isAnalyzing}
              onAnalysisComplete={handleAnalysisComplete}
              onReset={() => {
                setParts([]);
                setSelectedComponents(new Map());
                highestHierarchyRef.current = -1;
              }}
              onGetHighestHierarchy={() => highestHierarchyRef.current}
              onSetHighestHierarchy={(level) => {
                highestHierarchyRef.current = level;
              }}
            />
          </div>
        </motion.div>

        {/* Center Panel - PCB Viewer + Chat */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="flex-1 flex flex-col bg-zinc-950 overflow-hidden min-h-0"
        >
          {/* PCB Viewer - takes remaining space */}
          <div className="flex-1 overflow-hidden min-h-0">
            <PCBViewer selectedComponents={selectedComponents} />
          </div>
          {/* Design Chat - fixed height at bottom */}
          <div className="flex-shrink-0 border-t border-zinc-800 overflow-hidden">
            <DesignChat
              backendUrl={backendUrl}
              isAnalyzing={isAnalyzing}
              isCompleted={isCompleted}
              partsCount={parts.length}
              onQuerySent={(query, provider) => {
                setIsCompleted(false);
                handleQuerySent(query, provider);
              }}
              onQueryKilled={() => {
                setIsCompleted(false);
                handleQueryKilled();
              }}
            />
          </div>
        </motion.div>

        {/* Right Panel - Tabs with Parts List / Analysis */}
        <motion.div
          initial={{ x: 20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="w-[24vw] min-w-[320px] max-w-[480px] border-l border-zinc-800 bg-zinc-900/30 flex flex-col overflow-hidden h-full"
        >
          {/* Tab Navigation */}
          <div className="flex border-b border-zinc-800 bg-zinc-900/50">
            <button
              onClick={() => setActiveTab("design")}
              className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "design"
                  ? "text-neon-teal border-b-2 border-neon-teal bg-zinc-900/70"
                  : "text-neutral-blue hover:text-white"
              }`}
            >
              Design
            </button>
            <button
              onClick={() => setActiveTab("bom")}
              className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "bom"
                  ? "text-neon-teal border-b-2 border-neon-teal bg-zinc-900/70"
                  : "text-neutral-blue hover:text-white"
              }`}
            >
              BOM
            </button>
            <button
              onClick={() => setActiveTab("analysis")}
              className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "analysis"
                  ? "text-neon-teal border-b-2 border-neon-teal bg-zinc-900/70"
                  : "text-neutral-blue hover:text-white"
              }`}
            >
              Analysis
            </button>
            <button
              onClick={() => setActiveTab("templates")}
              className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "templates"
                  ? "text-neon-teal border-b-2 border-neon-teal bg-zinc-900/70"
                  : "text-neutral-blue hover:text-white"
              }`}
            >
              Templates
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto min-h-0">
            {activeTab === "design" && (
              <div className="p-4">
                <h3 className="text-lg font-semibold text-white mb-4">Design View</h3>
                <p className="text-sm text-neutral-blue">
                  Use the left panel to see component selection reasoning, and the center panel to visualize the PCB layout.
                </p>
              </div>
            )}
            {activeTab === "bom" && (
              <PartsList 
                parts={parts}
                onQuantityChange={(mpn, quantity) => {
                  setParts(prev => prev.map(p => p.mpn === mpn ? { ...p, quantity } : p));
                }}
                onPartRemove={(mpn) => {
                  setParts(prev => prev.filter(p => p.mpn !== mpn));
                  setSelectedComponents(prev => {
                    const newMap = new Map(prev);
                    for (const [key, value] of prev.entries()) {
                      if (value.partData?.mpn === mpn) {
                        newMap.delete(key);
                      }
                    }
                    return newMap;
                  });
                }}
                onNoteChange={(_mpn, _note) => {
                  // Notes are stored locally in PartsList component
                  // Could be extended to store in parent state if needed
                }}
                onLoadDesign={handleLoadDesign}
              />
            )}
            {activeTab === "analysis" && (
              <div className="space-y-4 p-4 overflow-y-auto">
                {designHealth && (
                  <DesignHealthScore
                    healthScore={designHealth.healthScore}
                    healthLevel={designHealth.healthLevel}
                    healthBreakdown={designHealth.healthBreakdown}
                  />
                )}
                <DesignValidationPanel
                  parts={parts}
                  connections={connections}
                  onPartAdd={(part: PartObject) => {
                    // CRITICAL: Check if part already exists before adding
                    const exists = parts.some(p => 
                      p.mpn === part.mpn && 
                      p.manufacturer === part.manufacturer
                    );
                    
                    if (exists) {
                      showToast(`${part.mpn} is already in the BOM`, "warning", 2000);
                      return;
                    }
                    
                    // CRITICAL: Ensure part has componentId
                    const partWithComponentId = {
                      ...part,
                      componentId: part.componentId || `added_${Date.now()}`,
                      quantity: part.quantity || 1
                    };
                    
                    // Add part to the BOM (parts array)
                    setParts(prev => {
                      const existingIndex = prev.findIndex(p => 
                        p.mpn === part.mpn && 
                        p.manufacturer === part.manufacturer &&
                        p.componentId === partWithComponentId.componentId
                      );
                      if (existingIndex >= 0) {
                        const updated = prev.map((p, idx) => 
                          idx === existingIndex ? { ...p, quantity: (p.quantity || 1) + 1 } : p
                        );
                        saveToHistory(updated);
                        return updated;
                      }
                      const updated = [...prev, partWithComponentId];
                      saveToHistory(updated);
                      return updated;
                    });
                    
                    // CRITICAL: Also add to selectedComponents Map for PCBViewer visualization
                    setSelectedComponents(prev => {
                      const newMap = new Map(prev);
                      const existingComponents = Array.from(prev.values()).map((c) => ({
                        id: c.id,
                        position: c.position,
                        size: c.size,
                      }));
                      
                      const organizedPosition = calculateComponentPosition(
                        partWithComponentId.componentId,
                        existingComponents,
                        prev.size
                      );
                      
                      newMap.set(partWithComponentId.componentId, {
                        id: partWithComponentId.componentId,
                        label: part.mpn.split("-")[0] || partWithComponentId.componentId,
                        position: organizedPosition,
                        partData: partWithComponentId,
                      });
                      return newMap;
                    });
                    
                    showToast(`Added ${part.mpn} to BOM`, "success", 2000);
                  }}
                />
                <BOMInsights 
                  parts={parts} 
                  connections={connections}
                  onPartAdd={(part) => {
                    // CRITICAL: Check if part already exists before adding
                    const exists = parts.some(p => 
                      p.mpn === part.mpn && 
                      p.manufacturer === part.manufacturer
                    );
                    
                    if (exists) {
                      showToast(`${part.mpn} is already in the BOM`, "warning", 2000);
                      return;
                    }
                    
                    // CRITICAL: Ensure part has componentId
                    const partWithComponentId = {
                      ...part,
                      componentId: part.componentId || `added_${Date.now()}`,
                      quantity: part.quantity || 1
                    };
                    
                    // Add part to the BOM (parts array)
                    setParts(prev => {
                      const existingIndex = prev.findIndex(p => 
                        p.mpn === part.mpn && 
                        p.manufacturer === part.manufacturer &&
                        p.componentId === partWithComponentId.componentId
                      );
                      if (existingIndex >= 0) {
                        const updated = prev.map((p, idx) => 
                          idx === existingIndex ? { ...p, quantity: (p.quantity || 1) + 1 } : p
                        );
                        // Save history with updated parts
                        saveToHistory(updated);
                        return updated;
                      }
                      const updated = [...prev, partWithComponentId];
                      // Save history with updated parts
                      saveToHistory(updated);
                      return updated;
                    });
                    
                    // CRITICAL: Also add to selectedComponents Map for PCBViewer visualization
                    setSelectedComponents(prev => {
                      const newMap = new Map(prev);
                      const existingComponents = Array.from(prev.values()).map((c) => ({
                        id: c.id,
                        position: c.position,
                        size: c.size,
                      }));
                      
                      const organizedPosition = calculateComponentPosition(
                        partWithComponentId.componentId,
                        existingComponents,
                        prev.size
                      );
                      
                      newMap.set(partWithComponentId.componentId, {
                        id: partWithComponentId.componentId,
                        label: part.mpn.split("-")[0] || partWithComponentId.componentId,
                        position: organizedPosition,
                        partData: partWithComponentId,
                      });
                      return newMap;
                    });
                    
                    showToast(`Added ${part.mpn} to BOM`, "success", 2000);
                  }}
                />
              </div>
            )}
            {activeTab === "templates" && (
              <div className="space-y-4 p-4 overflow-y-auto">
                <DesignTemplates
                  onTemplateSelect={(query) => {
                    try {
                      // Save current design as previous
                      setPreviousDesign([...parts]);
                      // Clear any previous errors
                      setError(null);
                      // Start new design with template - use current provider
                      handleQuerySent(query, provider);
                      setActiveTab("design");
                      showToast(`Starting template: ${query.substring(0, 50)}...`, "info", 2000);
                    } catch (error) {
                      const errorMessage = error instanceof Error ? error.message : "Unknown error";
                      showToast(`Template error: ${errorMessage}`, "error", 3000);
                      setError(errorMessage);
                      console.error("Template selection error:", error);
                    }
                  }}
                />
                {previousDesign && (
                  <DesignComparison
                    currentDesign={{ parts, connections, query: analysisQuery }}
                    previousDesign={{ parts: previousDesign, connections: [], query: "" }}
                    onRevert={() => {
                      setParts(previousDesign);
                      setPreviousDesign(null);
                      showToast("Reverted to previous design", "info", 2000);
                    }}
                  />
                )}
              </div>
            )}
          </div>
        </motion.div>
      </div>
      </div>
    </ErrorBoundary>
  );
}

