"""
AGV (Automated Guided Vehicle) Models

Models for AGV entities, paths, and navigation.
"""

from typing import Optional, List, Tuple
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, computed_field

from .warehouse import Position3D


class AGVStatus(str, Enum):
    """AGV operational status"""
    IDLE = "idle"
    MOVING = "moving"
    LOADING = "loading"
    UNLOADING = "unloading"
    CHARGING = "charging"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class AGVType(str, Enum):
    """Types of AGVs"""
    FORKLIFT = "forklift"
    PALLET_JACK = "pallet_jack"
    TUGGER = "tugger"
    AUTONOMOUS_MOBILE_ROBOT = "amr"
    CONVEYOR_CART = "conveyor_cart"


class PathNode(BaseModel):
    """Node in AGV navigation path"""
    id: str
    position: Position3D
    node_type: str = Field(default="waypoint", description="waypoint, pickup, dropoff, charging")
    accessible: bool = Field(default=True)
    occupied: bool = Field(default=False)
    
    # Traffic control
    max_vehicles: int = Field(default=1, ge=1, description="Max simultaneous vehicles at this node")
    current_vehicles: int = Field(default=0, ge=0)

    @computed_field
    @property
    def is_available(self) -> bool:
        """Check if node can accept more vehicles"""
        return self.accessible and self.current_vehicles < self.max_vehicles


class PathSegment(BaseModel):
    """Segment connecting two path nodes"""
    id: str
    start_node: str = Field(description="Start node ID")
    end_node: str = Field(description="End node ID")
    distance: float = Field(gt=0, description="Segment distance in meters")
    max_speed: float = Field(gt=0, default=2.0, description="Max speed in m/s")
    bidirectional: bool = Field(default=True)
    blocked: bool = Field(default=False)

    @computed_field
    @property
    def travel_time(self) -> float:
        """Calculate travel time in seconds"""
        return self.distance / self.max_speed


class NavigationPath(BaseModel):
    """Complete navigation path from origin to destination"""
    id: str
    origin_node: str
    destination_node: str
    nodes: List[str] = Field(description="Ordered list of node IDs")
    segments: List[PathSegment] = Field(default_factory=list)
    
    @computed_field
    @property
    def total_distance(self) -> float:
        """Calculate total path distance"""
        return sum(segment.distance for segment in self.segments)

    @computed_field
    @property
    def estimated_time(self) -> float:
        """Calculate estimated travel time in seconds"""
        return sum(segment.travel_time for segment in self.segments)

    @computed_field
    @property
    def is_valid(self) -> bool:
        """Check if path is valid (no blocked segments)"""
        return all(not segment.blocked for segment in self.segments)


class AGV(BaseModel):
    """Automated Guided Vehicle"""
    id: str = Field(description="Unique AGV identifier")
    name: str
    agv_type: AGVType = Field(default=AGVType.AUTONOMOUS_MOBILE_ROBOT)
    
    # Current state
    status: AGVStatus = Field(default=AGVStatus.IDLE)
    current_position: Position3D
    current_node: Optional[str] = None
    
    # Specifications
    max_speed: float = Field(gt=0, default=2.0, description="Maximum speed in m/s")
    max_load: float = Field(gt=0, default=1000, description="Max load capacity in kg")
    current_load: float = Field(ge=0, default=0, description="Current load in kg")
    battery_level: float = Field(ge=0, le=100, default=100, description="Battery percentage")
    
    # Navigation
    current_path: Optional[NavigationPath] = None
    target_node: Optional[str] = None
    
    # Mission tracking
    assigned_task_id: Optional[str] = None
    total_distance_traveled: float = Field(ge=0, default=0)
    last_update: datetime = Field(default_factory=datetime.now)

    @computed_field
    @property
    def is_available(self) -> bool:
        """Check if AGV is available for new task"""
        return (
            self.status == AGVStatus.IDLE and
            self.battery_level > 20 and
            self.assigned_task_id is None
        )

    @computed_field
    @property
    def load_percentage(self) -> float:
        """Calculate load utilization percentage"""
        return (self.current_load / self.max_load) * 100 if self.max_load > 0 else 0

    @computed_field
    @property
    def needs_charging(self) -> bool:
        """Check if AGV needs charging"""
        return self.battery_level < 30

    @computed_field
    @property
    def color_by_status(self) -> str:
        """Return color code based on status"""
        status_colors = {
            AGVStatus.IDLE: "#4caf50",  # Green
            AGVStatus.MOVING: "#2196f3",  # Blue
            AGVStatus.LOADING: "#ff9800",  # Orange
            AGVStatus.UNLOADING: "#ff9800",  # Orange
            AGVStatus.CHARGING: "#ffeb3b",  # Yellow
            AGVStatus.MAINTENANCE: "#9e9e9e",  # Gray
            AGVStatus.ERROR: "#f44336",  # Red
        }
        return status_colors.get(self.status, "#000000")


class AGVTask(BaseModel):
    """Task assigned to an AGV"""
    id: str
    agv_id: Optional[str] = None
    
    # Task details
    task_type: str = Field(description="pickup, delivery, restock, transfer")
    pickup_location: str = Field(description="Node ID for pickup")
    dropoff_location: str = Field(description="Node ID for dropoff")
    
    # Cargo details
    product_id: Optional[str] = None
    load_kg: float = Field(gt=0, description="Load weight in kg")
    
    # Status
    status: str = Field(default="pending", description="pending, assigned, in_progress, completed, failed")
    priority: int = Field(ge=1, le=10, default=5, description="Priority (1=low, 10=high)")
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.now)
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @computed_field
    @property
    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.status == "completed"

    @computed_field
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration if completed"""
        if self.assigned_at and self.completed_at:
            return (self.completed_at - self.assigned_at).total_seconds()
        return None


class AGVFleet(BaseModel):
    """Fleet of AGVs"""
    name: str
    vehicles: List[AGV] = Field(default_factory=list)
    tasks: List[AGVTask] = Field(default_factory=list)
    path_nodes: List[PathNode] = Field(default_factory=list)
    path_segments: List[PathSegment] = Field(default_factory=list)

    @computed_field
    @property
    def total_vehicles(self) -> int:
        """Get total number of vehicles"""
        return len(self.vehicles)

    @computed_field
    @property
    def available_vehicles(self) -> int:
        """Count available vehicles"""
        return sum(1 for agv in self.vehicles if agv.is_available)

    @computed_field
    @property
    def pending_tasks(self) -> int:
        """Count pending tasks"""
        return sum(1 for task in self.tasks if task.status == "pending")

    @computed_field
    @property
    def fleet_utilization(self) -> float:
        """Calculate fleet utilization percentage"""
        if not self.vehicles:
            return 0.0
        active = sum(1 for agv in self.vehicles if agv.status in [AGVStatus.MOVING, AGVStatus.LOADING, AGVStatus.UNLOADING])
        return (active / len(self.vehicles)) * 100

    @computed_field
    @property
    def average_battery_level(self) -> float:
        """Calculate average battery level across fleet"""
        if not self.vehicles:
            return 0.0
        return sum(agv.battery_level for agv in self.vehicles) / len(self.vehicles)
