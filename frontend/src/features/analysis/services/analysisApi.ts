/**
 * Analysis API Service
 * Handles calls to analysis endpoints (cost, supply chain, power, validation, etc.)
 * Updated to use /api/v1/ endpoints
 */

import apiClient from "../../shared/services/apiClient";
import configService from "../../shared/services/config";
import type {
  CostAnalysis,
  SupplyChainAnalysis,
  PowerAnalysis,
  DesignValidation,
  ManufacturingReadiness,
  SignalIntegrityAnalysis,
  ThermalAnalysis,
} from "../../shared/services/types";

export interface PartComparisonResult {
  parts: any[];
  comparison: {
    specs: Record<string, any[]>;
    differences: string[];
    recommendations: string[];
  };
}

export interface AlternativePart {
  id: string;
  name: string;
  compatibility_score: number;
  compatibility_notes: string[];
  cost_estimate?: { value: number; currency: string };
  availability_status?: string;
  lifecycle_status?: string;
}

// Re-export types from shared/services/types for backward compatibility
// These types are already imported above, so we just re-export them
export type {
  CostAnalysis,
  SupplyChainAnalysis,
  PowerAnalysis,
  DesignValidation,
  ManufacturingReadiness,
  SignalIntegrityAnalysis,
  ThermalAnalysis,
};

export interface DesignHealthScore {
  design_health_score: number;
  health_level: string;
  health_breakdown: {
    validation: {
      score: number;
      status: string;
      errors: number;
      warnings: number;
    };
    supply_chain: {
      score: number;
      status: string;
      risk_score: number;
    };
    manufacturing: {
      score: number;
      status: string;
      readiness: string;
    };
    thermal: {
      score: number;
      status: string;
      critical_issues: number;
      warnings: number;
    };
    cost: {
      score: number;
      status: string;
      optimization_opportunities: number;
    };
  };
}

/**
 * Compare multiple parts
 */
export async function compareParts(partIds: string[]): Promise<PartComparisonResult> {
  return apiClient.post<PartComparisonResult>("/api/v1/parts/compare", {
    part_ids: partIds,
  });
}

// Legacy function for backward compatibility
export async function comparePartsLegacy(partIds: string[]): Promise<PartComparisonResult> {
  const API_BASE = configService.getBackendUrl();
  const response = await fetch(`${API_BASE}/api/parts/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ part_ids: partIds }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to compare parts: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Find alternatives for a part
 */
export async function findAlternatives(
  partId: string,
  options?: { sameFootprint?: boolean; lowerCost?: boolean }
): Promise<{ alternatives: AlternativePart[] }> {
  const params = new URLSearchParams();
  if (options?.sameFootprint) params.append('same_footprint', 'true');
  if (options?.lowerCost) params.append('lower_cost', 'true');
  
  return apiClient.get<{ alternatives: AlternativePart[] }>(
    `/api/v1/parts/alternatives/${partId}?${params.toString()}`
  );
}

// Legacy function for backward compatibility
export async function findAlternativesLegacy(
  partId: string,
  options?: { sameFootprint?: boolean; lowerCost?: boolean }
): Promise<{ alternatives: AlternativePart[] }> {
  const API_BASE = configService.getBackendUrl();
  const params = new URLSearchParams();
  if (options?.sameFootprint) params.append('same_footprint', 'true');
  if (options?.lowerCost) params.append('lower_cost', 'true');
  
  const response = await fetch(`${API_BASE}/api/parts/alternatives/${partId}?${params}`);
  
  if (!response.ok) {
    throw new Error(`Failed to find alternatives: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Analyze BOM cost
 */
export async function analyzeCost(bomItems: any[]): Promise<CostAnalysis> {
  return apiClient.post<CostAnalysis>("/api/v1/analysis/cost", {
    bom_items: bomItems.map(item => ({
      part_data: item.part_data || item,
      quantity: item.quantity || 1,
    })),
  });
}

/**
 * Analyze supply chain risks
 */
export async function analyzeSupplyChain(bomItems: any[]): Promise<SupplyChainAnalysis> {
  return apiClient.post<SupplyChainAnalysis>("/api/v1/analysis/supply-chain", {
    bom_items: bomItems.map(item => ({
      part_data: item.part_data || item,
      quantity: item.quantity || 1,
    })),
  });
}

/**
 * Calculate power consumption
 */
export async function calculatePower(
  bomItems: any[],
  options?: {
    operatingModes?: Record<string, number>;
    batteryCapacityMah?: number;
    batteryVoltage?: number;
  }
): Promise<PowerAnalysis> {
  return apiClient.post<PowerAnalysis>("/api/v1/analysis/power", {
    bom_items: bomItems.map(item => ({
      part_data: item.part_data || item,
      quantity: item.quantity || 1,
    })),
    operating_modes: options?.operatingModes,
    battery_capacity_mah: options?.batteryCapacityMah,
    battery_voltage: options?.batteryVoltage,
  });
}

/**
 * Validate design
 */
export async function validateDesign(
  bomItems: any[],
  connections?: any[]
): Promise<DesignValidation> {
  return apiClient.post<DesignValidation>("/api/v1/analysis/validation", {
    bom_items: bomItems.map(item => ({
      part_data: item.part_data || item,
      quantity: item.quantity || 1,
    })),
    connections: (connections || []).map(conn => ({
      net_name: conn.net_name || conn.name,
      components: conn.components || [],
      pins: conn.pins || [],
      signal_type: conn.signal_type || conn.signalType,
    })),
  });
}

/**
 * Analyze manufacturing readiness
 */
export async function analyzeManufacturingReadiness(
  bomItems: any[],
  connections?: any[]
): Promise<ManufacturingReadiness> {
  return apiClient.post<ManufacturingReadiness>("/api/v1/analysis/manufacturing-readiness", {
    bom_items: bomItems.map(item => ({
      part_data: item.part_data || item,
      quantity: item.quantity || 1,
    })),
    connections: (connections || []).map(conn => ({
      net_name: conn.net_name || conn.name,
      components: conn.components || [],
      pins: conn.pins || [],
    })),
  });
}

/**
 * Analyze signal integrity
 */
export async function analyzeSignalIntegrity(
  bomItems: any[],
  connections?: any[],
  pcbThicknessMm?: number,
  traceWidthMils?: number
): Promise<SignalIntegrityAnalysis> {
  return apiClient.post<SignalIntegrityAnalysis>("/api/v1/analysis/signal-integrity", {
    bom_items: bomItems.map(item => ({
      part_data: item.part_data || item,
      quantity: item.quantity || 1,
    })),
    connections: (connections || []).map(conn => ({
      net_name: conn.net_name || conn.name,
      components: conn.components || [],
      pins: conn.pins || [],
    })),
    pcb_thickness_mm: pcbThicknessMm,
    trace_width_mils: traceWidthMils,
  });
}

/**
 * Analyze thermal characteristics
 */
export async function analyzeThermal(
  bomItems: any[],
  ambientTemp?: number,
  pcbAreaCm2?: number
): Promise<ThermalAnalysis> {
  return apiClient.post<ThermalAnalysis>("/api/v1/analysis/thermal", {
    bom_items: bomItems.map(item => ({
      part_data: item.part_data || item,
      quantity: item.quantity || 1,
    })),
    ambient_temp: ambientTemp,
    pcb_area_cm2: pcbAreaCm2,
  });
}

