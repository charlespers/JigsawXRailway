"""
Domain models for PCB design
Following IPC standards and engineering best practices
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class ComponentCategory(str, Enum):
    """Component categories following IPC standards"""
    MCU = "mcu"
    SENSOR = "sensor"
    POWER = "power"
    CONNECTOR = "connector"
    PASSIVE = "passive"
    INTERFACE = "interface"
    PROTECTION = "protection"
    CRYSTAL = "crystal"
    MECHANICAL = "mechanical"


class MountingType(str, Enum):
    """Mounting types"""
    SMT = "SMT"
    THROUGH_HOLE = "through_hole"
    BOTH = "both"


class Part(BaseModel):
    """Part model following IPC-2581 standards"""
    id: str
    name: str
    category: ComponentCategory
    manufacturer: str
    mfr_part_number: str
    description: str
    
    # Electrical specifications
    supply_voltage_range: Dict[str, Any] = Field(default_factory=dict)
    io_voltage_levels: Optional[List[float]] = None
    current_max: Dict[str, Any] = Field(default_factory=dict)
    power_rating: Optional[float] = None
    
    # Physical specifications
    package: str
    footprint: Optional[str] = None  # IPC-7351 compliant
    pinout: Dict[str, str] = Field(default_factory=dict)
    
    # Environmental
    operating_temp_range: Dict[str, float] = Field(default_factory=dict)
    rohs_compliant: bool = True
    msl_level: Optional[int] = None  # Moisture Sensitivity Level
    
    # Interface
    interface_type: List[str] = Field(default_factory=list)
    
    # Cost and availability
    cost_estimate: Dict[str, Any] = Field(default_factory=dict)
    availability_status: str = "in_stock"
    lifecycle_status: str = "active"
    lead_time_days: Optional[int] = None
    
    # Documentation
    datasheet_url: Optional[str] = None
    
    # Additional
    recommended_external_components: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class Requirements(BaseModel):
    """Extracted requirements from user query"""
    functional_requirements: List[str] = Field(default_factory=list)
    power_requirements: Dict[str, Any] = Field(default_factory=dict)
    interface_requirements: List[str] = Field(default_factory=list)
    environmental_requirements: Dict[str, Any] = Field(default_factory=dict)
    constraints: Dict[str, Any] = Field(default_factory=dict)


class Architecture(BaseModel):
    """System architecture"""
    anchor_block: Dict[str, Any] = Field(default_factory=dict)
    child_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies: List[Dict[str, Any]] = Field(default_factory=list)


class NetConnection(BaseModel):
    """Net connection following IPC-2581"""
    net_name: str
    net_class: str  # power, ground, signal, clock, differential
    connections: List[List[str]]  # [[part_id, pin_name], ...]
    current_estimate_amps: Optional[float] = None
    recommended_trace_width_mils: Optional[int] = None
    impedance_ohms: Optional[int] = None


class BOMItem(BaseModel):
    """BOM item following IPC-2581"""
    designator: str  # U1, R1, C1, etc.
    qty: int
    manufacturer: str
    mfr_part_number: str
    description: str
    category: str
    package: str
    footprint: str  # IPC-7351 compliant
    value: Optional[str] = None
    tolerance: Optional[str] = None
    mounting_type: MountingType = MountingType.SMT
    assembly_side: str = "top"  # top, bottom, both
    msl_level: Optional[int] = None
    unit_cost: float = 0.0
    extended_cost: float = 0.0
    datasheet_url: Optional[str] = None
    notes: str = ""
    
    class Config:
        use_enum_values = True


class BOM(BaseModel):
    """Bill of Materials following IPC-2581"""
    items: List[BOMItem] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Design(BaseModel):
    """Complete PCB design"""
    requirements: Requirements
    architecture: Architecture
    selected_parts: Dict[str, Any] = Field(default_factory=dict)  # Can be Part models or dicts
    connections: List[NetConnection] = Field(default_factory=list)
    bom: BOM
    design_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True

