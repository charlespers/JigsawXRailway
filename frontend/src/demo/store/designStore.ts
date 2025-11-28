/**
 * Design State Management Store
 * Centralized state management for design data using Zustand
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { PartObject } from '../services/types';

export interface DesignState {
  // Core design data
  parts: PartObject[];
  connections: any[];
  designHealth: {
    healthScore: number;
    healthLevel: string;
    healthBreakdown?: any;
  } | null;
  
  // Design metadata
  designId: string | null;
  sessionId: string | null;
  query: string;
  provider: 'openai' | 'xai';
  
  // UI state
  activeTab: 'design' | 'bom' | 'analysis' | 'templates';
  isAnalyzing: boolean;
  error: string | null;
  
  // History
  designHistory: PartObject[][];
  historyIndex: number;
  previousDesign: PartObject[] | null;
  
  // Selected components for visualization
  selectedComponents: Map<string, {
    id: string;
    label: string;
    position: { x: number; y: number };
    color?: string;
    size?: { w: number; h: number };
    partData?: PartObject;
  }>;
}

export interface DesignActions {
  // Part management
  setParts: (parts: PartObject[]) => void;
  addPart: (part: PartObject) => void;
  removePart: (componentId: string) => void;
  updatePart: (componentId: string, updates: Partial<PartObject>) => void;
  
  // Connections
  setConnections: (connections: any[]) => void;
  
  // Design health
  setDesignHealth: (health: DesignState['designHealth']) => void;
  
  // Metadata
  setDesignId: (id: string | null) => void;
  setSessionId: (id: string | null) => void;
  setQuery: (query: string) => void;
  setProvider: (provider: 'openai' | 'xai') => void;
  
  // UI state
  setActiveTab: (tab: DesignState['activeTab']) => void;
  setIsAnalyzing: (isAnalyzing: boolean) => void;
  setError: (error: string | null) => void;
  
  // History
  saveToHistory: () => void;
  undo: () => void;
  redo: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;
  
  // Selected components
  setSelectedComponents: (components: DesignState['selectedComponents']) => void;
  addSelectedComponent: (id: string, component: DesignState['selectedComponents'] extends Map<infer K, infer V> ? V : never) => void;
  removeSelectedComponent: (id: string) => void;
  
  // Reset
  reset: () => void;
  resetDesign: () => void;
}

const initialState: DesignState = {
  parts: [],
  connections: [],
  designHealth: null,
  designId: null,
  sessionId: null,
  query: '',
  provider: 'openai',
  activeTab: 'design',
  isAnalyzing: false,
  error: null,
  designHistory: [],
  historyIndex: -1,
  previousDesign: null,
  selectedComponents: new Map(),
};

export const useDesignStore = create<DesignState & DesignActions>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,
        
        // Part management
        setParts: (parts) => set({ parts }, false, 'setParts'),
        
        addPart: (part) => {
          const { parts } = get();
          // Check for duplicates
          const exists = parts.some(p => 
            p.mpn === part.mpn && 
            p.manufacturer === part.manufacturer
          );
          if (!exists) {
            set({ parts: [...parts, part] }, false, 'addPart');
          }
        },
        
        removePart: (componentId) => {
          const { parts } = get();
          set({ 
            parts: parts.filter(p => p.componentId !== componentId) 
          }, false, 'removePart');
        },
        
        updatePart: (componentId, updates) => {
          const { parts } = get();
          set({
            parts: parts.map(p => 
              p.componentId === componentId ? { ...p, ...updates } : p
            )
          }, false, 'updatePart');
        },
        
        // Connections
        setConnections: (connections) => 
          set({ connections }, false, 'setConnections'),
        
        // Design health
        setDesignHealth: (health) => 
          set({ designHealth: health }, false, 'setDesignHealth'),
        
        // Metadata
        setDesignId: (id) => set({ designId: id }, false, 'setDesignId'),
        setSessionId: (id) => set({ sessionId: id }, false, 'setSessionId'),
        setQuery: (query) => set({ query }, false, 'setQuery'),
        setProvider: (provider) => set({ provider }, false, 'setProvider'),
        
        // UI state
        setActiveTab: (tab) => set({ activeTab: tab }, false, 'setActiveTab'),
        setIsAnalyzing: (isAnalyzing) => 
          set({ isAnalyzing }, false, 'setIsAnalyzing'),
        setError: (error) => set({ error }, false, 'setError'),
        
        // History
        saveToHistory: () => {
          const { parts, designHistory, historyIndex } = get();
          const newHistory = designHistory.slice(0, historyIndex + 1);
          newHistory.push([...parts]);
          set({
            designHistory: newHistory,
            historyIndex: newHistory.length - 1,
            previousDesign: parts.length > 0 ? [...parts] : null,
          }, false, 'saveToHistory');
        },
        
        undo: () => {
          const { designHistory, historyIndex } = get();
          if (historyIndex > 0) {
            const newIndex = historyIndex - 1;
            set({
              parts: [...designHistory[newIndex]],
              historyIndex: newIndex,
            }, false, 'undo');
          }
        },
        
        redo: () => {
          const { designHistory, historyIndex } = get();
          if (historyIndex < designHistory.length - 1) {
            const newIndex = historyIndex + 1;
            set({
              parts: [...designHistory[newIndex]],
              historyIndex: newIndex,
            }, false, 'redo');
          }
        },
        
        canUndo: () => {
          const { historyIndex } = get();
          return historyIndex > 0;
        },
        
        canRedo: () => {
          const { designHistory, historyIndex } = get();
          return historyIndex < designHistory.length - 1;
        },
        
        // Selected components
        setSelectedComponents: (components) => 
          set({ selectedComponents: components }, false, 'setSelectedComponents'),
        
        addSelectedComponent: (id, component) => {
          const { selectedComponents } = get();
          const newMap = new Map(selectedComponents);
          newMap.set(id, component);
          set({ selectedComponents: newMap }, false, 'addSelectedComponent');
        },
        
        removeSelectedComponent: (id) => {
          const { selectedComponents } = get();
          const newMap = new Map(selectedComponents);
          newMap.delete(id);
          set({ selectedComponents: newMap }, false, 'removeSelectedComponent');
        },
        
        // Reset
        reset: () => set(initialState, false, 'reset'),
        
        resetDesign: () => set({
          parts: [],
          connections: [],
          designHealth: null,
          designId: null,
          error: null,
        }, false, 'resetDesign'),
      }),
      {
        name: 'design-store',
        // Only persist certain fields
        partialize: (state) => ({
          parts: state.parts,
          connections: state.connections,
          designHealth: state.designHealth,
          designId: state.designId,
          sessionId: state.sessionId,
          query: state.query,
          provider: state.provider,
        }),
      }
    ),
    { name: 'DesignStore' }
  )
);

