/**
 * Analysis API Service
 * Handles calls to analysis endpoints (cost, supply chain, power, validation, etc.)
 */

import configService from "./config";

const API_BASE = configService.getBackendUrl();

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

export interface CostAnalysis {
  total_cost: number;
  cost_by_category: Record<string, number>;
  high_cost_items: Array<{
    part_id: string;
    name: string;
    unit_cost: number;
    quantity: number;
    total_cost: number;
  }>;
  optimization_opportunities: Array<{
    part_id: string;
    part_name: string;
    current_cost: number;
    alternative: {
      id: string;
      name: string;
      cost: number;
    };
    savings_per_unit: number;
    total_savings: number;
  }>;
}

export interface SupplyChainAnalysis {
  risks: Array<{
    part_id: string;
    part_name: string;
    risks: string[];
    risk_score: number;
    quantity: number;
  }>;
  warnings: string[];
  risk_score: number;
  recommendations: string[];
}

export interface PowerAnalysis {
  total_power: number;
  power_by_rail: Record<string, number>;
  power_by_component: Array<{
    part_id: string;
    name: string;
    voltage: number;
    current: number;
    power: number;
    quantity: number;
    duty_cycle: number;
  }>;
  battery_life?: {
    battery_capacity_mah: number;
    battery_voltage: number;
    battery_energy_wh: number;
    total_power_w: number;
    estimated_hours: number;
    estimated_days: number;
  };
}

export interface DesignValidation {
  valid: boolean;
  issues: Array<{
    type: string;
    severity: "error" | "warning";
    message: string;
  }>;
  warnings: string[];
  compliance: {
    ipc_2221: boolean;
    ipc_7351: boolean;
    rohs: boolean;
    power_budget: boolean;
  };
}

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
  const response = await fetch(`${API_BASE}/api/analysis/cost`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ bom_items: bomItems }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to analyze cost: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Analyze supply chain risks
 */
export async function analyzeSupplyChain(bomItems: any[]): Promise<SupplyChainAnalysis> {
  const response = await fetch(`${API_BASE}/api/analysis/supply-chain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ bom_items: bomItems }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to analyze supply chain: ${response.statusText}`);
  }
  
  return response.json();
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
  const response = await fetch(`${API_BASE}/api/analysis/power`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      bom_items: bomItems,
      operating_modes: options?.operatingModes,
      battery_capacity_mah: options?.batteryCapacityMah,
      battery_voltage: options?.batteryVoltage,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to calculate power: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Validate design
 */
export async function validateDesign(
  bomItems: any[],
  connections?: any[]
): Promise<DesignValidation> {
  const response = await fetch(`${API_BASE}/api/validation/design`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      bom_items: bomItems,
      connections: connections || [],
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to validate design: ${response.statusText}`);
  }
  
  return response.json();
}

