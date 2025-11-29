/**
 * Demo package backward compatibility re-exports
 * Allows gradual migration from demo/ to features/
 */

// Design generation
export { default as ComponentGraph } from "../features/design-generation/components/ComponentGraph";
export { default as DesignChat } from "../features/design-generation/components/DesignChat";
export { default as PCBViewer } from "../features/design-generation/components/PCBViewer";
export { default as useDesignGeneration, useDesignGeneration as useDesignGenerationNamed } from "../features/design-generation/hooks/useDesignGeneration";
export * from "../features/design-generation/services/componentAnalysisApi";
export * from "../features/design-generation/services/designApi";
export * from "../features/design-generation/store/designStore";

// BOM management
export { default as PartsList } from "../features/bom-management/components/PartsList";
export { default as BOMInsights } from "../features/bom-management/components/BOMInsights";
export * from "../features/bom-management/components/bom";
export { default as useBOMManagement, useBOMManagement as useBOMManagementNamed } from "../features/bom-management/hooks/useBOMManagement";
export * from "../features/bom-management/utils/partNormalizer";

// Analysis
export * from "../features/analysis/components/analysis";
export * from "../features/analysis/components/validation";
export { default as useAnalysis, useAnalysis as useAnalysisNamed } from "../features/analysis/hooks/useAnalysis";
export * from "../features/analysis/services/analysisApi";

// Design tools
export { default as DesignComparison } from "../features/design-tools/components/DesignComparison";
export { default as DesignHealthScore } from "../features/design-tools/components/DesignHealthScore";
export { default as DesignTemplates } from "../features/design-tools/components/DesignTemplates";
export * from "../features/design-tools/components/visualization";
export * from "../features/design-tools/components/collaboration";
export * from "../features/design-tools/components/versioning";

// Shared
export * from "../features/shared/components";
// Explicitly export services to avoid conflicts with analysisApi types
export * from "../features/shared/services/apiClient";
export * from "../features/shared/services/config";
export { default as configService } from "../features/shared/services/config";
export * from "../features/shared/hooks/useIntersectionObserver";

// Keep original exports for files that haven't moved yet
export { default as JigsawDemo } from "./JigsawDemo";
export { default as JigsawDemoRefactored } from "./JigsawDemoRefactored";
export { default as JigsawIcon } from "./components/JigsawIcon";
export { default as SettingsPanel } from "./components/SettingsPanel";
export * from "./components/export";

