export interface PartObject {
  // Core fields (from data_mapper.py)
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
  
  // Extended fields (from data_mapper.py)
  tolerance?: string;
  lifecycle_status?: string;
  rohs_compliant?: boolean;
  lead_time_days?: number;
  mounting_type?: string;
  category?: string;
  
  // New BOM fields (from enhanced output_generator.py)
  footprint?: string; // IPC-7351 compliant footprint name
  assembly_side?: "top" | "bottom" | "both";
  msl_level?: string | number; // Moisture Sensitivity Level (1-6)
  alternate_part_numbers?: string[];
  assembly_notes?: string;
  test_point?: boolean;
  fiducial?: boolean;
  distributor_part_numbers?: Record<string, string>;
  temperature_rating?: string;
  availability_status?: string;
}
