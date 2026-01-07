"""
Warehouse Digital Twin - Core Data Models

This module defines Pydantic models for warehouse entities with geometry validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

from pydantic import BaseModel, Field, field_validator, computed_field
import numpy as np


class ZoneType(str, Enum):
    """Warehouse zone classifications"""
    A = "A"  # High-value, high-demand
    B = "B"  # Medium-value, medium-demand
    C = "C"  # Low-value, bulky items
    D = "D"  # Low-demand, long-term storage


class RackType(str, Enum):
    """Types of storage racks"""
    PALLET_RACKING = "pallet_racking"
    CANTILEVER = "cantilever"
    MOBILE = "mobile"
    MEZZANINE = "mezzanine"


class Position3D(BaseModel):
    """3D position coordinates"""
    x: float = Field(ge=0, description="X coordinate in meters")
    y: float = Field(ge=0, description="Y coordinate in meters")
    z: float = Field(ge=0, description="Z coordinate (height) in meters")

    @computed_field
    @property
    def distance_from_origin(self) -> float:
        """Calculate Euclidean distance from origin"""
        return float(np.sqrt(self.x**2 + self.y**2 + self.z**2))


class Dimensions3D(BaseModel):
    """3D dimensions"""
    width: float = Field(gt=0, description="Width in meters")
    depth: float = Field(gt=0, description="Depth in meters")
    height: float = Field(gt=0, description="Height in meters")
    length: Optional[float] = Field(None, gt=0, description="Length in meters (for racks)")

    @computed_field
    @property
    def volume(self) -> float:
        """Calculate volume in cubic meters"""
        if self.length:
            # For rectangular objects: length * width * height
            return self.length * self.width * self.height
        # For simple box: width * depth * height
        return self.width * self.depth * self.height

    @computed_field
    @property
    def floor_area(self) -> float:
        """Calculate floor area"""
        if self.length:
            return self.length * self.width
        return self.width * self.depth
    
    @computed_field
    @property
    def effective_length(self) -> float:
        """Get effective length dimension (length or depth)"""
        return self.length if self.length else self.depth


class Shelf(BaseModel):
    """Individual shelf unit within a rack"""
    id: str = Field(description="Unique shelf identifier (e.g., A1-R2-S3)")
    aisle_id: str = Field(description="Parent aisle identifier")
    rack_id: str = Field(description="Parent rack identifier")
    level_number: int = Field(ge=1, description="Vertical level/tier")
    position_in_rack: int = Field(ge=1, description="Horizontal position within rack")
    capacity: float = Field(gt=0, description="Storage capacity in cubic meters")
    occupied: bool = Field(default=False)
    product_id: Optional[str] = None
    load_kg: float = Field(ge=0, default=0, description="Current load in kg")
    max_load_kg: float = Field(gt=0, default=1000, description="Maximum load capacity in kg")

    @computed_field
    @property
    def is_overloaded(self) -> bool:
        """Check if shelf exceeds capacity"""
        return self.load_kg > self.max_load_kg

    @computed_field
    @property
    def utilization_percent(self) -> float:
        """Calculate shelf utilization"""
        return (self.load_kg / self.max_load_kg) * 100 if self.max_load_kg > 0 else 0


class RackLevel(BaseModel):
    """Individual level within a storage rack - can contain multiple shelves"""
    level_number: int = Field(ge=1, description="Level number (1 is ground level)")
    height_from_floor: float = Field(ge=0, description="Height from floor in meters")
    load_capacity: float = Field(gt=0, description="Load capacity in kg")
    occupied: bool = Field(default=False, description="Whether level is occupied")
    product_id: Optional[str] = None
    shelves: List[Shelf] = Field(default_factory=list, description="Shelves at this level")


class RackSystem(BaseModel):
    """Storage rack system with detailed structure"""
    id: str = Field(description="Unique rack identifier")
    type: RackType = Field(default=RackType.PALLET_RACKING)
    position: Position3D
    dimensions: Dimensions3D
    levels: List[RackLevel] = Field(default_factory=list)
    zone: Optional[ZoneType] = None

    @field_validator('levels')
    @classmethod
    def validate_levels(cls, v, info):
        """Ensure levels are properly ordered"""
        if v:
            heights = [level.height_from_floor for level in v]
            if heights != sorted(heights):
                raise ValueError("Rack levels must be ordered by height")
        return v

    @computed_field
    @property
    def total_capacity(self) -> float:
        """Calculate total storage capacity"""
        return sum(level.load_capacity for level in self.levels)

    @computed_field
    @property
    def utilization_rate(self) -> float:
        """Calculate utilization percentage"""
        if not self.levels:
            return 0.0
        occupied = sum(1 for level in self.levels if level.occupied)
        return (occupied / len(self.levels)) * 100


class Aisle(BaseModel):
    """Warehouse aisle"""
    id: str
    x_position: float = Field(ge=0)
    width: float = Field(gt=0, description="Aisle width in meters")
    length: float = Field(gt=0, description="Aisle length in meters")
    accessible: bool = Field(default=True, description="Whether aisle is currently accessible")


class WarehouseLayout(BaseModel):
    """Warehouse layout configuration - supports massive scale (100,000+ aisles/shelves)"""
    aisle_width: float = Field(gt=0, default=3.0, description="Standard aisle width")
    num_aisles: int = Field(ge=1, default=4, description="Number of aisles (no upper limit)")
    rack_bay_width: float = Field(gt=0, description="Width of each rack bay")
    rack_depth: float = Field(gt=0, default=1.2, description="Depth of racks")
    shelves_per_rack: int = Field(ge=1, default=5, description="Number of shelves per rack bay")
    aisle_positions: List[Aisle] = Field(default_factory=list)

    @field_validator('aisle_width')
    @classmethod
    def validate_aisle_width(cls, v):
        """Ensure aisle width meets safety standards"""
        if v < 2.0:
            raise ValueError("Aisle width must be at least 2.0m for safety")
        return v


class AccessPoint(BaseModel):
    """Entry or exit point for warehouse operations"""
    id: str = Field(description="Unique access point identifier")
    name: str = Field(description="Human-readable name")
    type: Literal["entry", "exit"] = Field(description="Point type")
    position: Position3D = Field(description="3D position in warehouse")
    capabilities: List[str] = Field(
        default_factory=list,
        description="Capabilities: standard, fragile, heavy, bulk, express"
    )
    base_cost: float = Field(ge=0, description="Cost to use this access point")
    capacity_per_hour: int = Field(gt=0, description="Throughput limit")
    active: bool = Field(default=True, description="Whether point is active")


class WarehouseConfig(BaseModel):
    """Complete warehouse configuration"""
    name: str = Field(description="Warehouse name/identifier")
    dimensions: Dimensions3D
    layout: WarehouseLayout
    storage_systems: List[RackSystem] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Multi-access point system
    entry_points: List[AccessPoint] = Field(default_factory=list, description="Entry points")
    exit_points: List[AccessPoint] = Field(default_factory=list, description="Exit points")

    @field_validator('dimensions')
    @classmethod
    def validate_warehouse_dimensions(cls, v):
        """Ensure warehouse dimensions are reasonable"""
        if v.height < 4.0:
            raise ValueError("Warehouse height must be at least 4.0m")
        if v.width < 10.0 or (v.length and v.length < 10.0):
            raise ValueError("Warehouse width and length must be at least 10.0m")
        return v
    
    @property
    def warehouse_length(self) -> float:
        """Get warehouse effective length (convenience method)"""
        return self.dimensions.effective_length

    @computed_field
    @property
    def total_storage_capacity(self) -> float:
        """Calculate total storage capacity across all racks"""
        return sum(rack.total_capacity for rack in self.storage_systems)

    @computed_field
    @property
    def overall_utilization(self) -> float:
        """Calculate overall warehouse utilization"""
        if not self.storage_systems:
            return 0.0
        return sum(rack.utilization_rate for rack in self.storage_systems) / len(
            self.storage_systems
        )

    @computed_field
    @property
    def total_aisles(self) -> int:
        """Get total number of aisles"""
        return self.layout.num_aisles

    @computed_field
    @property
    def total_shelves(self) -> int:
        """Calculate total number of shelves across all racks"""
        total = 0
        for rack in self.storage_systems:
            for level in rack.levels:
                total += len(level.shelves)
        return total

    @computed_field
    @property
    def estimated_total_shelves(self) -> int:
        """
        Estimate total shelves based on configuration (useful for large warehouses).
        Formula: num_aisles * 2 (sides) * num_racks_per_aisle * shelves_per_rack
        """
        # Rough estimate: 2 racks per aisle (both sides)
        racks_per_aisle = 2
        if self.storage_systems:
            avg_levels = sum(len(r.levels) for r in self.storage_systems) / len(self.storage_systems)
        else:
            avg_levels = self.layout.shelves_per_rack if hasattr(self.layout, 'shelves_per_rack') else 5
        
        # Estimate shelves per level (typically 10-20 shelf positions per level)
        shelves_per_level = 15
        
        return int(self.layout.num_aisles * racks_per_aisle * avg_levels * shelves_per_level)
    
    def add_default_access_points(self):
        """
        Add default entry and exit points based on warehouse dimensions.
        
        Entry Points:
        1. Main Entry (Front-Left)
        2. Receiving Dock (Back-Left)
        3. Express Entry (Front-Right)
        4. Bulk Entry (Mid-Left)
        
        Exit Points:
        1. Shipping Dock A (Front-Right)
        2. Shipping Dock B (Back-Right)
        3. Express Dock (Front-Center)
        4. Return Center (Mid-Right)
        """
        width = self.dimensions.width
        length = self.warehouse_length
        
        # Entry Points
        self.entry_points = [
            AccessPoint(
                id="entry_main",
                name="Main Entry",
                type="entry",
                position=Position3D(x=5.0, y=5.0, z=0.0),
                capabilities=["standard", "fragile", "heavy", "bulk", "express"],
                base_cost=2.0,
                capacity_per_hour=200,
                active=True
            ),
            AccessPoint(
                id="entry_receiving",
                name="Receiving Dock",
                type="entry",
                position=Position3D(x=5.0, y=length - 5.0, z=0.0),
                capabilities=["heavy", "bulk"],
                base_cost=1.5,
                capacity_per_hour=150,
                active=True
            ),
            AccessPoint(
                id="entry_express",
                name="Express Entry",
                type="entry",
                position=Position3D(x=width - 5.0, y=5.0, z=0.0),
                capabilities=["fragile", "express"],
                base_cost=3.0,
                capacity_per_hour=100,
                active=True
            ),
            AccessPoint(
                id="entry_bulk",
                name="Bulk Entry",
                type="entry",
                position=Position3D(x=5.0, y=length / 2, z=0.0),
                capabilities=["bulk"],
                base_cost=1.0,
                capacity_per_hour=300,
                active=True
            )
        ]
        
        # Exit Points
        self.exit_points = [
            AccessPoint(
                id="exit_shipping_a",
                name="Shipping Dock A",
                type="exit",
                position=Position3D(x=width - 5.0, y=5.0, z=0.0),
                capabilities=["standard", "fragile", "heavy", "bulk", "express"],
                base_cost=2.5,
                capacity_per_hour=200,
                active=True
            ),
            AccessPoint(
                id="exit_shipping_b",
                name="Shipping Dock B",
                type="exit",
                position=Position3D(x=width - 5.0, y=length - 5.0, z=0.0),
                capabilities=["standard", "heavy"],
                base_cost=2.0,
                capacity_per_hour=250,
                active=True
            ),
            AccessPoint(
                id="exit_express",
                name="Express Dock",
                type="exit",
                position=Position3D(x=width / 2, y=5.0, z=0.0),
                capabilities=["fragile", "express"],
                base_cost=4.0,
                capacity_per_hour=80,
                active=True
            ),
            AccessPoint(
                id="exit_return",
                name="Return Center",
                type="exit",
                position=Position3D(x=width - 5.0, y=length / 2, z=0.0),
                capabilities=["standard", "fragile", "heavy", "bulk", "express"],
                base_cost=1.5,
                capacity_per_hour=120,
                active=True
            )
        ]


class Product(BaseModel):
    """Product/Item in warehouse"""
    item_id: str = Field(description="Unique product identifier")
    description: str
    category: str
    profit_per_unit: float = Field(ge=0)
    daily_demand: int = Field(ge=0)
    stock_level: int = Field(ge=0)
    holding_cost_per_unit_day: float = Field(ge=0)
    turnover_ratio: float = Field(gt=0)
    size_score: float = Field(gt=0, description="Physical size metric")
    
    # Allocation results
    predicted_zone: Optional[ZoneType] = None
    final_zone: Optional[ZoneType] = None
    shelf: Optional[str] = None
    rack_id: Optional[str] = None
    position: Optional[Position3D] = None
    
    # Dates
    restock_date: Optional[str] = None
    discount_date: Optional[str] = None
    
    # ML features
    category_encoded: Optional[int] = None
    cluster: Optional[int] = None
    cluster_name: Optional[str] = None
    
    # Additional fields for CSV import
    weight_kg: Optional[float] = Field(None, ge=0, description="Weight in kilograms")
    is_fragile: Optional[bool] = Field(None, description="Whether item is fragile")
    handling_cost_per_unit: Optional[float] = Field(None, ge=0, description="Handling cost per unit")
    picking_time_seconds: Optional[float] = Field(None, ge=0, description="Time to pick item in seconds")
    storage_location_id: Optional[str] = Field(None, description="Storage location ID from CSV")

    @computed_field
    @property
    def days_until_restock(self) -> float:
        """Calculate days until restock needed"""
        if self.daily_demand > 0:
            return self.stock_level / self.daily_demand
        return float('inf')

    @computed_field
    @property
    def total_value(self) -> float:
        """Calculate total inventory value"""
        return self.profit_per_unit * self.stock_level

    @computed_field
    @property
    def space_required(self) -> float:
        """Calculate space requirement"""
        return self.stock_level * self.size_score
