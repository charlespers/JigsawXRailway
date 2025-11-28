/**
 * Design Store (Zustand)
 * Centralized state management for design data
 */

import { create } from "zustand";
import type { PartObject } from "../services/types";

interface DesignState {
  // Design data
  parts: PartObject[];
  connections: any[];
  designHealth: {
    healthScore: number;
    healthLevel: string;
    healthBreakdown?: any;
  } | null;

  // UI state
  activeTab: "design" | "bom" | "analysis" | "templates";
  isAnalyzing: boolean;
  error: string | null;
  selectedComponents: Map<
    string,
    {
      id: string;
      label: string;
      position: { x: number; y: number };
      color?: string;
      size?: { w: number; h: number };
      partData?: PartObject;
    }
  >;

  // Actions
  setParts: (parts: PartObject[] | ((prev: PartObject[]) => PartObject[])) => void;
  setConnections: (connections: any[]) => void;
  setDesignHealth: (health: DesignState["designHealth"]) => void;
  setActiveTab: (tab: DesignState["activeTab"]) => void;
  setIsAnalyzing: (isAnalyzing: boolean) => void;
  setError: (error: string | null) => void;
  setSelectedComponents: (
    components:
      | Map<string, DesignState["selectedComponents"] extends Map<string, infer T> ? T : never>
      | ((
          prev: Map<string, DesignState["selectedComponents"] extends Map<string, infer T> ? T : never>
        ) => Map<string, DesignState["selectedComponents"] extends Map<string, infer T> ? T : never>)
  ) => void;
}

export const useDesignStore = create<DesignState>((set) => ({
  // Initial state
  parts: [],
  connections: [],
  designHealth: null,
  activeTab: "design",
  isAnalyzing: false,
  error: null,
  selectedComponents: new Map(),

  // Actions
  setParts: (parts) =>
    set((state) => ({
      parts: typeof parts === "function" ? parts(state.parts) : parts,
    })),
  setConnections: (connections) => set({ connections }),
  setDesignHealth: (designHealth) => set({ designHealth }),
  setActiveTab: (activeTab) => set({ activeTab }),
  setIsAnalyzing: (isAnalyzing) => set({ isAnalyzing }),
  setError: (error) => set({ error }),
  setSelectedComponents: (components) =>
    set((state) => ({
      selectedComponents:
        typeof components === "function"
          ? components(state.selectedComponents)
          : components,
    })),
}));
