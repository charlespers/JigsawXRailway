/**
 * Refactored JigsawDemo Component
 * Uses new architecture with hooks and state management
 */

import React, { useState, useEffect } from "react";
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

// New components
import { 
  BOMEditor, 
  BOMTable, 
  BOMCostTracking, 
  BOMGrouping, 
  BOMSupplierLinks,
  BOMVersioning,
  BOMSupplierManagement,
  BOMExport,
} from "./components/bom";
import { SchematicView, NetlistView } from "./components/visualization";
import { AnalysisDashboard } from "./components/analysis";
import { ExportDialog } from "./components/export";
import { VersionHistory } from "./components/versioning";
import { CommentsPanel, ShareDialog } from "./components/collaboration";

import { useToast } from "./components/Toast";
import { useDesignStore } from "./store/designStore";
import { useDesignGeneration, useBOMManagement } from "./hooks";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import configService from "./services/config";

export interface JigsawDemoProps {
  backendUrl?: string;
  initialQuery?: string;
  className?: string;
  height?: string;
}

export default function JigsawDemoRefactored({
  backendUrl,
  initialQuery = "",
  className = "",
  height = "100vh",
}: JigsawDemoProps) {
  // Configure API services
  useEffect(() => {
    const url = backendUrl || configService.getBackendUrl();
    if (backendUrl) {
      configService.updateConfig({ backendUrl: url });
    }
  }, [backendUrl]);

  // Use Zustand store
  const {
    parts,
    connections,
    designHealth,
    activeTab,
    isAnalyzing,
    error,
    setActiveTab,
    setError,
    selectedComponents,
    setSelectedComponents,
  } = useDesignStore();

  // Use custom hooks
  const { handleQuerySent, cancelAnalysis } = useDesignGeneration();
  const { addPartToBOM, removePartFromBOM, updatePartInBOM } = useBOMManagement();
  const { showToast, ToastComponent } = useToast();

  // Local UI state
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [selectedComponentId, setSelectedComponentId] = useState<string | null>(null);
  const [provider, setProvider] = useState<"openai" | "xai">("openai");

  // Handle component selection from PCB viewer
  const handleComponentSelected = (
    componentId: string,
    partData: any,
    position?: { x: number; y: number },
    hierarchyOffset?: number
  ) => {
    addPartToBOM(partData);
    
    // Update selected components map
    setSelectedComponents((prev) => {
      const newMap = new Map(prev);
      newMap.set(componentId, {
        id: componentId,
        label: partData.mpn.split("-")[0] || componentId,
        position: position || { x: 0, y: 0 },
        partData,
      });
      return newMap;
    });
  };

  return (
    <ErrorBoundary>
      <div
        className={`flex flex-col h-screen bg-dark-bg text-white ${className}`}
        style={{ height }}
      >
        {/* Header */}
        <header className="flex items-center justify-between p-4 border-b border-dark-border bg-dark-surface">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-white">Jigsaw PCB Design</h1>
            <Badge variant="outline" className="text-xs">
              Enterprise Edition
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowShareDialog(true)}
            >
              Share
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowExportDialog(true)}
            >
              Export
            </Button>
            <SettingsPanel backendUrl={backendUrl || configService.getBackendUrl()} defaultProvider="openai" />
          </div>
        </header>

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Sidebar */}
          <aside className="w-64 border-r border-dark-border bg-dark-surface overflow-y-auto">
            <div className="p-4 space-y-2">
              <button
                onClick={() => setActiveTab("design")}
                className={`w-full text-left px-3 py-2 rounded ${
                  activeTab === "design"
                    ? "bg-neon-teal/20 text-neon-teal"
                    : "text-neutral-blue hover:text-white"
                }`}
              >
                Design
              </button>
              <button
                onClick={() => setActiveTab("bom")}
                className={`w-full text-left px-3 py-2 rounded ${
                  activeTab === "bom"
                    ? "bg-neon-teal/20 text-neon-teal"
                    : "text-neutral-blue hover:text-white"
                }`}
              >
                BOM Management
              </button>
              <button
                onClick={() => setActiveTab("analysis")}
                className={`w-full text-left px-3 py-2 rounded ${
                  activeTab === "analysis"
                    ? "bg-neon-teal/20 text-neon-teal"
                    : "text-neutral-blue hover:text-white"
                }`}
              >
                Analysis
              </button>
              <button
                onClick={() => setActiveTab("templates")}
                className={`w-full text-left px-3 py-2 rounded ${
                  activeTab === "templates"
                    ? "bg-neon-teal/20 text-neon-teal"
                    : "text-neutral-blue hover:text-white"
                }`}
              >
                Templates
              </button>
            </div>
          </aside>

          {/* Content Area */}
          <main className="flex-1 overflow-y-auto p-6">
            {activeTab === "design" && (
              <div className="space-y-4">
                <DesignChat
                  onQuerySent={(query, selectedProvider) => {
                    setProvider(selectedProvider);
                    handleQuerySent(query, selectedProvider);
                  }}
                />
                {error && <ErrorDisplay error={error} onDismiss={() => setError(null)} />}
                {parts.length > 0 && (
                  <>
                    {/* ComponentGraph and PCBViewer use selectedComponents from store */}
                    <PartsList
                      parts={parts}
                      onPartRemove={removePartFromBOM}
                    />
                  </>
                )}
              </div>
            )}

            {activeTab === "bom" && (
              <div className="space-y-4">
                <BOMEditor parts={parts} />
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <BOMCostTracking parts={parts} />
                  <BOMGrouping parts={parts} groupBy="category" />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <BOMVersioning parts={parts} />
                  <BOMSupplierManagement parts={parts} />
                </div>
                <BOMExport parts={parts} connections={connections} />
                <BOMSupplierLinks parts={parts} />
              </div>
            )}

            {activeTab === "analysis" && (
              <div className="space-y-4">
                <AnalysisDashboard />
                <DesignValidationPanel
                  parts={parts}
                  connections={connections}
                  onPartAdd={addPartToBOM}
                />
                <BOMInsights parts={parts} connections={connections} />
              </div>
            )}

            {activeTab === "templates" && (
              <DesignTemplates onTemplateSelect={(query) => {
                // Use current provider setting
                handleQuerySent(query, provider);
              }} />
            )}
          </main>
        </div>

        {/* Modals */}
        {showExportDialog && (
          <ExportDialog
            parts={parts}
            connections={connections}
            onClose={() => setShowExportDialog(false)}
          />
        )}

        {showShareDialog && (
          <ShareDialog
            designId="current"
            onClose={() => setShowShareDialog(false)}
          />
        )}

        <ToastComponent />
      </div>
    </ErrorBoundary>
  );
}

