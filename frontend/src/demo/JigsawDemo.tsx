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

import { useState, useEffect, useRef } from "react";
import { motion } from "motion/react";
import ComponentGraph from "./components/ComponentGraph";
import PCBViewer from "./components/PCBViewer";
import PartsList from "./components/PartsList";
import DesignChat from "./components/DesignChat";
import SettingsPanel from "./components/SettingsPanel";
import BOMInsights from "./components/BOMInsights";
import type { PartObject } from "./services/types";
import { componentAnalysisApi } from "./services";

export interface JigsawDemoProps {
  /** Backend API URL (e.g., "http://localhost:3001") */
  backendUrl?: string;
  /** Initial query to start analysis with */
  initialQuery?: string;
  /** Custom CSS class name */
  className?: string;
  /** Height of the demo container */
  height?: string;
}

export default function JigsawDemo({
  backendUrl = "http://localhost:3001",
  initialQuery = "",
  className = "",
  height = "100vh",
}: JigsawDemoProps) {
  // Configure API services
  useEffect(() => {
    if (backendUrl) {
      componentAnalysisApi.updateConfig({ baseUrl: backendUrl });
    }
  }, [backendUrl]);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisQuery, setAnalysisQuery] = useState<string>(initialQuery);
  const [provider, setProvider] = useState<"openai" | "xai">("openai");
  const [parts, setParts] = useState<PartObject[]>([]);
  const [activeTab, setActiveTab] = useState<"design" | "bom" | "analysis">("design");
  const [connections, setConnections] = useState<any[]>([]);
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
  const handleQuerySent = (query: string, selectedProvider: "openai" | "xai" = "openai") => {
    // Reset if this is a new query (different from previous)
    if (previousQueryRef.current !== query && previousQueryRef.current !== "") {
      setParts([]);
      setSelectedComponents(new Map());
      highestHierarchyRef.current = -1;
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
    hierarchyLevel: number
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
    position?: { x: number; y: number },
    hierarchyOffset?: number
  ) => {
    setParts((prev) => {
      const existingIndex = prev.findIndex((p) => p.mpn === partData.mpn);
      if (existingIndex >= 0) {
        return prev;
      }
      return [...prev, { ...partData, quantity: partData.quantity || 1 }];
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

  const handleAnalysisComplete = () => {
    setIsAnalyzing(false);
  };

  // Load settings from localStorage
  useEffect(() => {
    const savedBackendUrl = localStorage.getItem("demo_backend_url");
    const savedProvider = localStorage.getItem("demo_provider");
    if (savedBackendUrl) {
      componentAnalysisApi.updateConfig({ baseUrl: savedBackendUrl });
    }
    // Only use saved provider if it's valid, otherwise default to "openai"
    if (savedProvider === "openai" || savedProvider === "xai") {
      setProvider(savedProvider);
    } else {
      // Ensure default is "openai" if localStorage has invalid value
      setProvider("openai");
      localStorage.setItem("demo_provider", "openai");
    }
  }, []);

  return (
    <div
      className={`h-screen bg-zinc-950 text-white flex flex-col overflow-hidden ${className}`}
      style={{ height }}
    >
      <SettingsPanel
        backendUrl={backendUrl}
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
              onQuerySent={handleQuerySent}
              onQueryKilled={handleQueryKilled}
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
                onNoteChange={(mpn, note) => {
                  // Notes are stored locally in PartsList component
                  // Could be extended to store in parent state if needed
                }}
              />
            )}
            {activeTab === "analysis" && (
              <BOMInsights 
                parts={parts} 
                connections={connections}
                onPartAdd={(part) => {
                  // Add part to the BOM
                  setParts(prev => {
                    const existingIndex = prev.findIndex(p => p.mpn === part.mpn);
                    if (existingIndex >= 0) {
                      return prev.map((p, idx) => 
                        idx === existingIndex ? { ...p, quantity: (p.quantity || 1) + 1 } : p
                      );
                    }
                    return [...prev, { ...part, quantity: part.quantity || 1 }];
                  });
                }}
              />
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

