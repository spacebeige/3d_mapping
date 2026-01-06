"""
A* Pathfinding Algorithm for AGV Navigation

Implements A* algorithm for finding optimal paths in warehouse environments.
Handles large-scale warehouses with 100,000+ nodes efficiently.
"""

import heapq
from typing import Dict, List, Optional, Tuple, Set
import numpy as np

from models.agv import PathNode, PathSegment, NavigationPath
from models.warehouse import Position3D


class PathfindingGrid:
    """
    Efficient pathfinding grid for warehouse navigation.
    Optimized for large-scale environments.
    """
    
    def __init__(self, nodes: List[PathNode], segments: List[PathSegment]):
        self.nodes: Dict[str, PathNode] = {node.id: node for node in nodes}
        self.segments: List[PathSegment] = segments
        self.adjacency: Dict[str, List[Tuple[str, PathSegment]]] = {}
        self._build_adjacency()
    
    def _build_adjacency(self):
        """Build adjacency list for efficient pathfinding"""
        self.adjacency = {node_id: [] for node_id in self.nodes}
        
        for segment in self.segments:
            if not segment.blocked:
                self.adjacency[segment.start_node].append((segment.end_node, segment))
                if segment.bidirectional:
                    self.adjacency[segment.end_node].append((segment.start_node, segment))
    
    def heuristic(self, node_id_a: str, node_id_b: str) -> float:
        """
        Heuristic function for A* (Euclidean distance).
        """
        pos_a = self.nodes[node_id_a].position
        pos_b = self.nodes[node_id_b].position
        
        dx = pos_a.x - pos_b.x
        dy = pos_a.y - pos_b.y
        dz = pos_a.z - pos_b.z
        
        return np.sqrt(dx**2 + dy**2 + dz**2)
    
    def find_path(
        self, 
        start_node: str, 
        goal_node: str,
        avoid_nodes: Optional[Set[str]] = None
    ) -> Optional[NavigationPath]:
        """
        Find optimal path using A* algorithm.
        
        Args:
            start_node: Starting node ID
            goal_node: Destination node ID
            avoid_nodes: Set of node IDs to avoid (optional)
            
        Returns:
            NavigationPath if found, None otherwise
        """
        if start_node not in self.nodes or goal_node not in self.nodes:
            return None
        
        if start_node == goal_node:
            return NavigationPath(
                id=f"path_{start_node}_to_{goal_node}",
                origin_node=start_node,
                destination_node=goal_node,
                nodes=[start_node],
                segments=[]
            )
        
        avoid_nodes = avoid_nodes or set()
        
        # Priority queue: (f_score, node_id)
        open_set = [(0, start_node)]
        
        # Track came_from for path reconstruction
        came_from: Dict[str, Tuple[str, PathSegment]] = {}
        
        # Cost from start to node
        g_score: Dict[str, float] = {start_node: 0}
        
        # Estimated total cost
        f_score: Dict[str, float] = {start_node: self.heuristic(start_node, goal_node)}
        
        # Track nodes in open set for efficiency
        open_set_nodes: Set[str] = {start_node}
        
        while open_set:
            current_f, current = heapq.heappop(open_set)
            open_set_nodes.discard(current)
            
            # Goal reached
            if current == goal_node:
                return self._reconstruct_path(came_from, current, start_node, goal_node)
            
            # Explore neighbors
            for neighbor, segment in self.adjacency.get(current, []):
                # Skip unavailable nodes
                if neighbor in avoid_nodes or not self.nodes[neighbor].is_available:
                    continue
                
                # Calculate tentative g_score
                tentative_g_score = g_score[current] + segment.distance
                
                # Check if this path is better
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = (current, segment)
                    g_score[neighbor] = tentative_g_score
                    f = tentative_g_score + self.heuristic(neighbor, goal_node)
                    f_score[neighbor] = f
                    
                    if neighbor not in open_set_nodes:
                        heapq.heappush(open_set, (f, neighbor))
                        open_set_nodes.add(neighbor)
        
        # No path found
        return None
    
    def _reconstruct_path(
        self, 
        came_from: Dict[str, Tuple[str, PathSegment]], 
        current: str,
        start: str,
        goal: str
    ) -> NavigationPath:
        """Reconstruct path from came_from dictionary"""
        nodes = [current]
        segments = []
        
        while current in came_from:
            prev_node, segment = came_from[current]
            nodes.append(prev_node)
            segments.append(segment)
            current = prev_node
        
        nodes.reverse()
        segments.reverse()
        
        return NavigationPath(
            id=f"path_{start}_to_{goal}",
            origin_node=start,
            destination_node=goal,
            nodes=nodes,
            segments=segments
        )
    
    def find_multiple_paths(
        self, 
        start_node: str,
        goal_nodes: List[str],
        max_paths: int = 5
    ) -> List[NavigationPath]:
        """
        Find paths to multiple destinations, sorted by distance.
        Useful for task assignment optimization.
        """
        paths = []
        
        for goal in goal_nodes:
            path = self.find_path(start_node, goal)
            if path:
                paths.append(path)
        
        # Sort by total distance
        paths.sort(key=lambda p: p.total_distance)
        
        return paths[:max_paths]
    
    def find_nearest_available_node(
        self, 
        from_node: str,
        node_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Find nearest available node of specified type.
        Useful for finding nearest charging station, pickup point, etc.
        """
        candidates = []
        
        for node_id, node in self.nodes.items():
            if node.is_available:
                if node_type is None or node.node_type == node_type:
                    distance = self.heuristic(from_node, node_id)
                    candidates.append((distance, node_id))
        
        if not candidates:
            return None
        
        candidates.sort()
        return candidates[0][1]


class CollisionDetector:
    """Detect and prevent AGV collisions"""
    
    @staticmethod
    def check_collision(
        pos1: Position3D,
        pos2: Position3D,
        safety_distance: float = 1.5
    ) -> bool:
        """
        Check if two positions are within collision distance.
        
        Args:
            pos1: First position
            pos2: Second position
            safety_distance: Minimum safe distance in meters
            
        Returns:
            True if collision risk exists
        """
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        dz = pos1.z - pos2.z
        
        distance = np.sqrt(dx**2 + dy**2 + dz**2)
        return distance < safety_distance
    
    @staticmethod
    def predict_collision(
        pos1: Position3D,
        velocity1: Tuple[float, float, float],
        pos2: Position3D,
        velocity2: Tuple[float, float, float],
        time_horizon: float = 5.0,
        safety_distance: float = 1.5
    ) -> bool:
        """
        Predict if two moving AGVs will collide within time horizon.
        
        Args:
            pos1: Current position of AGV 1
            velocity1: Velocity vector of AGV 1 (vx, vy, vz)
            pos2: Current position of AGV 2
            velocity2: Velocity vector of AGV 2 (vx, vy, vz)
            time_horizon: Look-ahead time in seconds
            safety_distance: Minimum safe distance
            
        Returns:
            True if collision predicted
        """
        # Sample positions at intervals
        dt = 0.5  # Time step
        steps = int(time_horizon / dt)
        
        for i in range(steps):
            t = i * dt
            
            # Predict future positions
            future_pos1 = Position3D(
                x=pos1.x + velocity1[0] * t,
                y=pos1.y + velocity1[1] * t,
                z=pos1.z + velocity1[2] * t
            )
            
            future_pos2 = Position3D(
                x=pos2.x + velocity2[0] * t,
                y=pos2.y + velocity2[1] * t,
                z=pos2.z + velocity2[2] * t
            )
            
            if CollisionDetector.check_collision(future_pos1, future_pos2, safety_distance):
                return True
        
        return False


def generate_warehouse_navigation_grid(
    warehouse_length: float,
    warehouse_width: float,
    num_aisles: int,
    aisle_width: float,
    node_spacing: float = 5.0
) -> Tuple[List[PathNode], List[PathSegment]]:
    """
    Generate navigation grid for warehouse.
    Optimized to handle 100,000+ nodes efficiently.
    
    Args:
        warehouse_length: Length in meters
        warehouse_width: Width in meters
        num_aisles: Number of aisles
        aisle_width: Width of each aisle
        node_spacing: Distance between nodes in meters
        
    Returns:
        Tuple of (nodes, segments) for pathfinding
    """
    nodes = []
    segments = []
    
    # Calculate aisle positions
    total_aisle_space = num_aisles * aisle_width
    rack_space = warehouse_width - total_aisle_space
    
    # Generate nodes along aisles
    node_id_counter = 0
    node_positions = {}
    
    for aisle_idx in range(num_aisles):
        # Calculate x position of aisle center
        aisle_x = (aisle_idx + 0.5) * (warehouse_width / num_aisles)
        
        # Create nodes along aisle length
        num_nodes_in_aisle = int(warehouse_length / node_spacing)
        
        for node_idx in range(num_nodes_in_aisle):
            y_pos = node_idx * node_spacing
            node_id = f"node_a{aisle_idx}_n{node_idx}"
            
            node = PathNode(
                id=node_id,
                position=Position3D(x=aisle_x, y=y_pos, z=0),
                node_type="waypoint"
            )
            nodes.append(node)
            node_positions[node_id] = (aisle_idx, node_idx)
            
            # Create segment to previous node in same aisle
            if node_idx > 0:
                prev_id = f"node_a{aisle_idx}_n{node_idx-1}"
                segment = PathSegment(
                    id=f"seg_{prev_id}_to_{node_id}",
                    start_node=prev_id,
                    end_node=node_id,
                    distance=node_spacing,
                    bidirectional=True
                )
                segments.append(segment)
    
    # Add cross-aisle connections
    for aisle_idx in range(num_aisles - 1):
        num_nodes_in_aisle = int(warehouse_length / node_spacing)
        
        # Connect every N nodes between adjacent aisles
        cross_connect_interval = 5
        for node_idx in range(0, num_nodes_in_aisle, cross_connect_interval):
            node_id_1 = f"node_a{aisle_idx}_n{node_idx}"
            node_id_2 = f"node_a{aisle_idx + 1}_n{node_idx}"
            
            if node_id_1 in node_positions and node_id_2 in node_positions:
                cross_distance = warehouse_width / num_aisles
                
                segment = PathSegment(
                    id=f"seg_cross_{node_id_1}_to_{node_id_2}",
                    start_node=node_id_1,
                    end_node=node_id_2,
                    distance=cross_distance,
                    bidirectional=True
                )
                segments.append(segment)
    
    return nodes, segments
