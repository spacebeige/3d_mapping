"""
Geospatial Data Models

Pydantic models for warehouse locations, routes, and supply chain nodes.
"""

from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, computed_field
import numpy as np


class CoordinateSystem(str, Enum):
    """Coordinate reference systems"""
    WGS84 = "EPSG:4326"  # Standard GPS coordinates
    WEB_MERCATOR = "EPSG:3857"  # Web mapping


class FacilityType(str, Enum):
    """Types of facilities in supply chain"""
    WAREHOUSE = "warehouse"
    DISTRIBUTION_CENTER = "distribution_center"
    RETAIL_STORE = "retail_store"
    SUPPLIER = "supplier"
    HUB = "hub"


class GeoCoordinate(BaseModel):
    """Geographic coordinate pair"""
    latitude: float = Field(ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(ge=-180, le=180, description="Longitude in decimal degrees")
    elevation: Optional[float] = Field(None, description="Elevation in meters above sea level")

    @computed_field
    @property
    def as_tuple(self) -> Tuple[float, float]:
        """Return as (lat, lon) tuple"""
        return (self.latitude, self.longitude)

    @computed_field
    @property
    def as_geojson_point(self) -> Dict[str, Any]:
        """Convert to GeoJSON Point format"""
        coordinates = [self.longitude, self.latitude]
        if self.elevation is not None:
            coordinates.append(self.elevation)
        return {
            "type": "Point",
            "coordinates": coordinates
        }

    def distance_to(self, other: "GeoCoordinate") -> float:
        """
        Calculate great circle distance to another coordinate using Haversine formula.
        Returns distance in kilometers.
        """
        R = 6371  # Earth's radius in kilometers

        lat1, lon1 = np.radians(self.latitude), np.radians(self.longitude)
        lat2, lon2 = np.radians(other.latitude), np.radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))

        return R * c


class WarehouseLocation(BaseModel):
    """Warehouse facility with geographic location"""
    id: str = Field(description="Unique warehouse identifier")
    name: str
    facility_type: FacilityType = Field(default=FacilityType.WAREHOUSE)
    coordinate: GeoCoordinate
    
    # Facility metrics
    capacity: float = Field(gt=0, description="Storage capacity in cubic meters")
    current_utilization: float = Field(ge=0, le=100, default=0, description="Utilization percentage")
    
    # Operational data
    daily_throughput: Optional[int] = Field(None, ge=0, description="Daily items processed")
    staff_count: Optional[int] = Field(None, ge=0)
    operating_cost_daily: Optional[float] = Field(None, ge=0)
    
    # Address info
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

    @computed_field
    @property
    def utilization_color(self) -> str:
        """Return color code based on utilization"""
        if self.current_utilization >= 90:
            return "#d32f2f"  # Red - Critical
        elif self.current_utilization >= 75:
            return "#f57c00"  # Orange - High
        elif self.current_utilization >= 50:
            return "#fbc02d"  # Yellow - Medium
        else:
            return "#388e3c"  # Green - Low

    @computed_field
    @property
    def elevation_meters(self) -> float:
        """Get elevation for 3D visualization"""
        # Scale utilization to elevation (0-100% -> 0-500m for visualization)
        return self.current_utilization * 5


class Route(BaseModel):
    """Supply chain route between facilities"""
    id: str
    name: Optional[str] = None
    origin: WarehouseLocation
    destination: WarehouseLocation
    
    # Route characteristics
    distance_km: Optional[float] = Field(None, ge=0, description="Route distance in kilometers")
    estimated_time_hours: Optional[float] = Field(None, ge=0)
    
    # Operational metrics
    daily_shipments: int = Field(ge=0, default=0)
    avg_load_kg: Optional[float] = Field(None, ge=0)
    cost_per_km: Optional[float] = Field(None, ge=0)
    
    # Route metadata
    transport_mode: Optional[str] = Field(None, description="truck, rail, air, sea")
    active: bool = Field(default=True)
    
    @computed_field
    @property
    def calculated_distance(self) -> float:
        """Calculate distance if not provided"""
        if self.distance_km is not None:
            return self.distance_km
        return self.origin.coordinate.distance_to(self.destination.coordinate)

    @computed_field
    @property
    def total_daily_cost(self) -> Optional[float]:
        """Calculate total daily shipping cost"""
        if self.cost_per_km is not None and self.daily_shipments > 0:
            return self.calculated_distance * self.cost_per_km * self.daily_shipments
        return None

    @computed_field
    @property
    def as_geojson_linestring(self) -> Dict[str, Any]:
        """Convert route to GeoJSON LineString"""
        return {
            "type": "LineString",
            "coordinates": [
                [self.origin.coordinate.longitude, self.origin.coordinate.latitude],
                [self.destination.coordinate.longitude, self.destination.coordinate.latitude]
            ]
        }

    @computed_field
    @property
    def arc_color(self) -> List[int]:
        """Color based on shipment volume"""
        if self.daily_shipments >= 100:
            return [255, 0, 0, 200]  # Red - High volume
        elif self.daily_shipments >= 50:
            return [255, 165, 0, 200]  # Orange - Medium volume
        else:
            return [0, 255, 0, 200]  # Green - Low volume


class DemandPoint(BaseModel):
    """Geographic point with demand data"""
    id: str
    coordinate: GeoCoordinate
    demand_volume: float = Field(ge=0, description="Demand volume/intensity")
    product_category: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @computed_field
    @property
    def elevation_by_demand(self) -> float:
        """Scale elevation based on demand for 3D visualization"""
        return min(self.demand_volume * 10, 1000)  # Cap at 1000m


class SupplyChainNetwork(BaseModel):
    """Complete supply chain network"""
    name: str
    facilities: List[WarehouseLocation] = Field(default_factory=list)
    routes: List[Route] = Field(default_factory=list)
    demand_points: List[DemandPoint] = Field(default_factory=list)
    
    # Network bounds (for map viewport)
    min_lat: Optional[float] = None
    max_lat: Optional[float] = None
    min_lon: Optional[float] = None
    max_lon: Optional[float] = None

    @computed_field
    @property
    def center_coordinate(self) -> Optional[GeoCoordinate]:
        """Calculate network center point"""
        if not self.facilities:
            return None
        
        avg_lat = sum(f.coordinate.latitude for f in self.facilities) / len(self.facilities)
        avg_lon = sum(f.coordinate.longitude for f in self.facilities) / len(self.facilities)
        
        return GeoCoordinate(latitude=avg_lat, longitude=avg_lon)

    @computed_field
    @property
    def total_network_capacity(self) -> float:
        """Sum of all facility capacities"""
        return sum(f.capacity for f in self.facilities)

    def update_bounds(self):
        """Update geographic bounds based on facilities"""
        if self.facilities:
            lats = [f.coordinate.latitude for f in self.facilities]
            lons = [f.coordinate.longitude for f in self.facilities]
            
            self.min_lat = min(lats)
            self.max_lat = max(lats)
            self.min_lon = min(lons)
            self.max_lon = max(lons)
