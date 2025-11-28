/**
 * Backend Type Definitions
 * TypeScript types aligned with backend Pydantic schemas
 */

// Aligned with api/schemas/common.py
export interface BOMItem {
  part_data: Record<string, any>;
  quantity: number;
  designator?: string;
  reference?: string;
}

export interface Connection {
  net_name: string;
  components: string[];
  pins: string[];
  signal_type?: string;
}

// Aligned with api/schemas/design.py
export interface ComponentAnalysisRequest {
  query: string;
  provider: "openai" | "xai";
  sessionId?: string;
  contextQueryId?: string;
  context?: string;
}

export interface ComponentAnalysisEvent {
  type: "reasoning" | "selection" | "complete" | "error" | "heartbeat";
  componentId?: string;
  componentName?: string;
  reasoning?: string;
  hierarchyLevel?: number;
  partData?: Record<string, any>;
  message?: string;
}

// Aligned with api/schemas/analysis.py
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
    component?: string | null;
    message: string;
    current?: string | null;
    required?: string | null;
    recommendation?: string;
    fixable?: boolean;
    category?: string;
  }>;
  warnings: Array<string | {
    type: string;
    severity: "error" | "warning";
    component?: string | null;
    message: string;
    current?: string | null;
    required?: string | null;
    recommendation?: string;
    fixable?: boolean;
    category?: string;
  }>;
  compliance: {
    ipc_2221: boolean;
    ipc_7351: boolean;
    rohs: boolean;
    power_budget: boolean;
  };
  summary?: {
    error_count: number;
    warning_count: number;
    compliance_score: number;
  };
  fix_suggestions?: Array<Record<string, any>>;
}

export interface ManufacturingReadiness {
  dfm_checks: Record<string, any>;
  assembly_complexity: {
    complexity_score: number;
    factors: string[];
  };
  test_point_coverage: {
    coverage_percentage: number;
    recommendations: string[];
  };
  panelization_recommendations: string[];
  overall_readiness: "ready" | "needs_review" | "not_ready";
  recommendations: string[];
}

export interface SignalIntegrityAnalysis {
  high_speed_signals: Array<{
    part_id: string;
    name: string;
    interface: string;
    calculated_impedance_ohms: number;
    required_impedance_ohms: number;
    impedance_ok: boolean;
    recommendation: string;
  }>;
  impedance_recommendations: Array<{
    interface: string;
    part: string;
    current_impedance: number;
    required_impedance: number;
    recommendation: string;
  }>;
  emi_emc_recommendations: string[];
  routing_recommendations: string[];
  decoupling_analysis: {
    adequate: boolean;
    recommendations: string[];
  };
}

export interface ThermalAnalysis {
  component_thermal: Record<string, {
    power_dissipation_w: number;
    junction_temp_c: number;
    max_temp_c: number;
    thermal_ok: boolean;
  }>;
  thermal_issues: Array<{
    part_id: string;
    junction_temp_c: number;
    max_temp_c: number;
    power_dissipation_w: number;
    issue: string;
  }>;
  total_thermal_issues: number;
  total_power_dissipation_w: number;
  recommendations: string[];
}

// Error response (aligned with api/schemas/common.py)
export interface ErrorResponse {
  error: string;
  code?: string;
  details?: Record<string, any>;
}

