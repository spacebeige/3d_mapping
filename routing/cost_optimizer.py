"""
Cost-Optimized Routing System

Calculates optimal routes considering:
- Item characteristics (weight, fragility, size)
- Handling costs
- Access point costs
- Distance and time
"""

from typing import List, Optional, Literal, Dict, Tuple
from dataclasses import dataclass, field
import numpy as np

from models.warehouse import (
    WarehouseConfig, Product, AccessPoint, Position3D
)
from core.pathfinding import PathfindingGrid, generate_warehouse_navigation_grid


@dataclass
class RouteSegment:
    """Single segment of a route"""
    start: Position3D
    end: Position3D
    distance: float
    cost: float
    description: str


@dataclass
class OptimalRoute:
    """Complete optimal route with cost breakdown"""
    product: Product
    start_position: Position3D
    end_position: Position3D
    entry_point: Optional[AccessPoint] = None
    exit_point: Optional[AccessPoint] = None
    
    # Path details
    waypoints: List[Position3D] = field(default_factory=list)
    segments: List[RouteSegment] = field(default_factory=list)
    total_distance: float = 0.0
    
    # Cost breakdown
    base_distance_cost: float = 0.0
    weight_cost: float = 0.0
    fragility_cost: float = 0.0
    size_cost: float = 0.0
    access_point_cost: float = 0.0
    handling_cost: float = 0.0
    time_cost: float = 0.0
    total_cost: float = 0.0
    
    # Metadata
    estimated_time_seconds: float = 0.0
    operation: str = "retrieve"


class CostOptimizedRouter:
    """
    Cost-optimized route finder for warehouse operations.
    
    Considers multiple factors:
    - Distance (base cost)
    - Weight (heavy items cost more)
    - Fragility (fragile items require special handling)
    - Size (large items need more space)
    - Access point costs and capabilities
    - Handling costs
    - Time costs
    """
    
    # Cost parameters
    BASE_DISTANCE_COST_PER_METER = 0.10  # $0.10 per meter
    TIME_COST_PER_SECOND = 0.05  # $0.05 per second
    WEIGHT_THRESHOLD_KG = 20.0  # Heavy if > 20kg
    WEIGHT_MULTIPLIER = 1.5  # 50% cost increase
    FRAGILITY_MULTIPLIER = 1.2  # 20% cost increase
    SIZE_THRESHOLD = 3.0  # Large if size_score > 3.0
    SIZE_MULTIPLIER = 1.3  # 30% cost increase
    AGV_SPEED_MPS = 1.5  # 1.5 meters per second
    
    def __init__(self, warehouse_config: WarehouseConfig):
        """
        Initialize cost optimizer.
        
        Args:
            warehouse_config: Warehouse configuration with access points
        """
        self.warehouse = warehouse_config
        self.agv_pathfinder: Optional[PathfindingGrid] = None
        
        # Initialize pathfinding grid if needed
        try:
            # Extract required arguments from warehouse_config
            length = getattr(warehouse_config, 'warehouse_length', None)
            width = getattr(warehouse_config.dimensions, 'width', None)
            num_aisles = getattr(warehouse_config.layout, 'num_aisles', None)
            aisle_width = getattr(warehouse_config.layout, 'aisle_width', None)
            if None in (length, width, num_aisles, aisle_width):
                raise ValueError("Missing required warehouse configuration for pathfinding grid.")
            self.agv_pathfinder = generate_warehouse_navigation_grid(
                length, width, num_aisles, aisle_width
            )
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize pathfinding: {e}")
    
    def find_optimal_route(
        self,
        product: Product,
        start_position: Optional[Position3D] = None,
        goal_position: Optional[Position3D] = None,
        operation: Literal["store", "retrieve", "relocate"] = "retrieve"
    ) -> OptimalRoute:
        """
        Find cost-optimized route for product.
        
        Args:
            product: Product to route
            start_position: Starting position (uses product position if None)
            goal_position: Goal position (uses optimal exit if None)
            operation: Operation type
            
        Returns:
            OptimalRoute with complete cost breakdown
        """
        # Determine start position
        if start_position is None:
            start_position = product.position or Position3D(x=0, y=0, z=0)
        
        # Determine item characteristics
        is_fragile = self._is_item_fragile(product)
        is_heavy = self._is_item_heavy(product)
        is_large = self._is_item_large(product)
        
        # Determine required capabilities
        required_capabilities = self._get_required_capabilities(
            product, is_fragile, is_heavy, is_large
        )
        
        # Find best entry/exit points
        if operation == "retrieve":
            # Product at shelf -> find best exit
            exit_point = self._find_best_exit_point(
                start_position, required_capabilities, product
            )
            entry_point = None
            end_position = exit_point.position if exit_point else Position3D(
                x=self.warehouse.dimensions.width - 5, y=5, z=0
            )
        elif operation == "store":
            # Product at entry -> find path to shelf
            entry_point = self._find_best_entry_point(
                start_position, required_capabilities, product
            )
            exit_point = None
            end_position = goal_position or start_position
        else:  # relocate
            entry_point = None
            exit_point = None
            end_position = goal_position or start_position
        
        # Calculate path
        waypoints = self._calculate_path(start_position, end_position)
        total_distance = self._calculate_total_distance(waypoints)
        
        # Calculate costs
        base_distance_cost = total_distance * self.BASE_DISTANCE_COST_PER_METER
        
        # Weight penalty
        weight_cost = 0.0
        if is_heavy:
            weight_cost = base_distance_cost * (self.WEIGHT_MULTIPLIER - 1.0)
        
        # Fragility penalty
        fragility_cost = 0.0
        if is_fragile:
            fragility_cost = base_distance_cost * (self.FRAGILITY_MULTIPLIER - 1.0)
        
        # Size penalty
        size_cost = 0.0
        if is_large:
            size_cost = base_distance_cost * (self.SIZE_MULTIPLIER - 1.0)
        
        # Access point cost
        access_point_cost = 0.0
        if entry_point:
            access_point_cost += entry_point.base_cost
        if exit_point:
            access_point_cost += exit_point.base_cost
        
        # Handling cost
        handling_cost = product.handling_cost_per_unit or 0.0
        
        # Time cost
        estimated_time = (total_distance / self.AGV_SPEED_MPS) + (
            product.picking_time_seconds or 0.0
        )
        time_cost = estimated_time * self.TIME_COST_PER_SECOND
        
        # Total cost
        total_cost = (
            base_distance_cost +
            weight_cost +
            fragility_cost +
            size_cost +
            access_point_cost +
            handling_cost +
            time_cost
        )
        
        # Create route segments
        segments = self._create_segments(waypoints, base_distance_cost)
        
        # Build optimal route
        route = OptimalRoute(
            product=product,
            start_position=start_position,
            end_position=end_position,
            entry_point=entry_point,
            exit_point=exit_point,
            waypoints=waypoints,
            segments=segments,
            total_distance=total_distance,
            base_distance_cost=base_distance_cost,
            weight_cost=weight_cost,
            fragility_cost=fragility_cost,
            size_cost=size_cost,
            access_point_cost=access_point_cost,
            handling_cost=handling_cost,
            time_cost=time_cost,
            total_cost=total_cost,
            estimated_time_seconds=estimated_time,
            operation=operation
        )
        
        return route
    
    def _is_item_fragile(self, product: Product) -> bool:
        """Check if item is fragile"""
        if product.is_fragile is not None:
            return product.is_fragile
        
        # Check by category
        fragile_categories = {
            "Electronics", "VR Headsets", "Quantum Devices",
            "Telemedicine", "Wearables"
        }
        return product.category in fragile_categories
    
    def _is_item_heavy(self, product: Product) -> bool:
        """Check if item is heavy (> 20kg)"""
        if product.weight_kg is not None:
            return product.weight_kg > self.WEIGHT_THRESHOLD_KG
        
        # Estimate by category
        heavy_categories = {"Automotive"}
        return product.category in heavy_categories
    
    def _is_item_large(self, product: Product) -> bool:
        """Check if item is large"""
        return product.size_score > self.SIZE_THRESHOLD
    
    def _get_required_capabilities(
        self, product: Product, is_fragile: bool, is_heavy: bool, is_large: bool
    ) -> List[str]:
        """Determine required access point capabilities"""
        capabilities = ["standard"]
        
        if is_fragile:
            capabilities.append("fragile")
        if is_heavy:
            capabilities.append("heavy")
        if is_large:
            capabilities.append("bulk")
        
        # Check for express (high-value items)
        if product.profit_per_unit > 100:
            capabilities.append("express")
        
        return capabilities
    
    def _find_best_exit_point(
        self,
        start_position: Position3D,
        required_capabilities: List[str],
        product: Product
    ) -> Optional[AccessPoint]:
        """
        Find best exit point considering capabilities and cost.
        
        Args:
            start_position: Current position
            required_capabilities: Required capabilities
            product: Product being routed
            
        Returns:
            Best exit point or None
        """
        if not self.warehouse.exit_points:
            return None
        
        best_exit = None
        best_cost = float('inf')
        
        for exit_point in self.warehouse.exit_points:
            if not exit_point.active:
                continue
            
            # Check if exit supports required capabilities
            if not self._supports_capabilities(exit_point, required_capabilities):
                continue
            
            # Calculate distance to exit
            distance = self._euclidean_distance(start_position, exit_point.position)
            
            # Calculate total cost to use this exit
            route_cost = (
                distance * self.BASE_DISTANCE_COST_PER_METER +
                exit_point.base_cost
            )
            
            if route_cost < best_cost:
                best_cost = route_cost
                best_exit = exit_point
        
        return best_exit
    
    def _find_best_entry_point(
        self,
        goal_position: Position3D,
        required_capabilities: List[str],
        product: Product
    ) -> Optional[AccessPoint]:
        """Find best entry point considering capabilities and cost"""
        if not self.warehouse.entry_points:
            return None
        
        best_entry = None
        best_cost = float('inf')
        
        for entry_point in self.warehouse.entry_points:
            if not entry_point.active:
                continue
            
            # Check capabilities
            if not self._supports_capabilities(entry_point, required_capabilities):
                continue
            
            # Calculate distance
            distance = self._euclidean_distance(entry_point.position, goal_position)
            
            # Calculate cost
            route_cost = (
                distance * self.BASE_DISTANCE_COST_PER_METER +
                entry_point.base_cost
            )
            
            if route_cost < best_cost:
                best_cost = route_cost
                best_entry = entry_point
        
        return best_entry
    
    def _supports_capabilities(
        self, access_point: AccessPoint, required_capabilities: List[str]
    ) -> bool:
        """Check if access point supports required capabilities"""
        # Standard points support all
        if "standard" in access_point.capabilities and len(required_capabilities) == 1:
            return True
        
        # Check specific capabilities
        for cap in required_capabilities:
            if cap != "standard" and cap not in access_point.capabilities:
                return False
        
        return True
    
    def _euclidean_distance(self, p1: Position3D, p2: Position3D) -> float:
        """Calculate Euclidean distance between two points"""
        dx = p1.x - p2.x
        dy = p1.y - p2.y
        dz = p1.z - p2.z
        return float(np.sqrt(dx**2 + dy**2 + dz**2))
    
    def _calculate_path(
        self, start: Position3D, end: Position3D
    ) -> List[Position3D]:
        """
        Calculate path waypoints from start to end.
        Uses A* if available, otherwise straight line.
        
        Args:
            start: Start position
            end: End position
            
        Returns:
            List of waypoints
        """
        # For now, use simple waypoint path
        # In production, would use A* pathfinding
        waypoints = [start]
        
        # Add intermediate waypoints (simplified)
        mid_x = (start.x + end.x) / 2
        mid_y = (start.y + end.y) / 2
        
        if abs(start.x - end.x) > 5 or abs(start.y - end.y) > 5:
            waypoints.append(Position3D(x=mid_x, y=start.y, z=start.z))
            waypoints.append(Position3D(x=mid_x, y=mid_y, z=start.z))
            waypoints.append(Position3D(x=end.x, y=mid_y, z=end.z))
        
        waypoints.append(end)
        
        return waypoints
    
    def _calculate_total_distance(self, waypoints: List[Position3D]) -> float:
        """Calculate total distance along waypoints"""
        if len(waypoints) < 2:
            return 0.0
        
        total = 0.0
        for i in range(len(waypoints) - 1):
            total += self._euclidean_distance(waypoints[i], waypoints[i + 1])
        
        return total
    
    def _create_segments(
        self, waypoints: List[Position3D], total_cost: float
    ) -> List[RouteSegment]:
        """Create route segments from waypoints"""
        segments = []
        
        for i in range(len(waypoints) - 1):
            start = waypoints[i]
            end = waypoints[i + 1]
            distance = self._euclidean_distance(start, end)
            
            # Distribute cost proportionally
            segment_cost = (distance / sum(
                self._euclidean_distance(waypoints[j], waypoints[j + 1])
                for j in range(len(waypoints) - 1)
            )) * total_cost if len(waypoints) > 1 else total_cost
            
            segments.append(RouteSegment(
                start=start,
                end=end,
                distance=distance,
                cost=segment_cost,
                description=f"Segment {i+1}"
            ))
        
        return segments
