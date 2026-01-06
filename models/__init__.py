"""
Data Models for Warehouse Digital Twin System

This package contains Pydantic models for:
- Warehouse structures (racks, aisles, shelves) - Supports 100,000+ aisles/shelves
- Products and inventory
- Geospatial data (locations, routes, networks)
- AGV (Automated Guided Vehicles) and pathfinding
"""

from .warehouse import (
    ZoneType,
    RackType,
    Position3D,
    Dimensions3D,
    Shelf,
    RackLevel,
    RackSystem,
    Aisle,
    WarehouseLayout,
    WarehouseConfig,
    Product,
)

from .geospatial import (
    CoordinateSystem,
    FacilityType,
    GeoCoordinate,
    WarehouseLocation,
    Route,
    DemandPoint,
    SupplyChainNetwork,
)

from .agv import (
    AGVStatus,
    AGVType,
    PathNode,
    PathSegment,
    NavigationPath,
    AGV,
    AGVTask,
    AGVFleet,
)

__all__ = [
    # Warehouse models
    "ZoneType",
    "RackType",
    "Position3D",
    "Dimensions3D",
    "Shelf",
    "RackLevel",
    "RackSystem",
    "Aisle",
    "WarehouseLayout",
    "WarehouseConfig",
    "Product",
    # Geospatial models
    "CoordinateSystem",
    "FacilityType",
    "GeoCoordinate",
    "WarehouseLocation",
    "Route",
    "DemandPoint",
    "SupplyChainNetwork",
    # AGV models
    "AGVStatus",
    "AGVType",
    "PathNode",
    "PathSegment",
    "NavigationPath",
    "AGV",
    "AGVTask",
    "AGVFleet",
]
