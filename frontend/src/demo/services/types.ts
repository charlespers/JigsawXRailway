/**
 * PartObject Interface
 * Aligned with backend Pydantic schema (api/schemas/common.py)
 * CRITICAL: componentId must be preserved for frontend-backend compatibility
 */
export interface PartObject {
  // CRITICAL: Component identification - maps to backend block_name
  componentId: string;  // Must be preserved for frontend-backend compatibility
  
  // Core fields (aligned with backend PartObject schema)
  mpn: string;
  manufacturer: string;
  description: string;
  price: number;
  currency?: string;
  voltage?: string;
  package?: string;
  interfaces?: string[];
  datasheet?: string;
  quantity?: number;
  
  // Extended fields (aligned with backend)
  tolerance?: string;
  lifecycle_status?: string;
  rohs_compliant?: boolean;
  lead_time_days?: number;
  mounting_type?: string;
  category?: string;
  
  // BOM fields (aligned with backend PartObject schema)
  footprint?: string; // IPC-7351 compliant footprint name
  assembly_side?: "top" | "bottom" | "both";
  msl_level?: string | number; // Moisture Sensitivity Level (1-6)
  alternate_part_numbers?: string[];
  assembly_notes?: string;
  test_point?: boolean;
  fiducial?: boolean;
  distributor_part_numbers?: Record<string, string>;
  temperature_rating?: number | string; // Can be number (C) or string
  availability_status?: string;
}
