"""
3D Geospatial Map Generator using PyDeck

Creates beautiful interactive 3D maps with warehouse locations, routes, and demand heat maps.
"""

from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import pydeck as pdk
import numpy as np

from models.geospatial import (
    WarehouseLocation,
    Route,
    DemandPoint,
    SupplyChainNetwork,
    GeoCoordinate,
    FacilityType
)


class Map3DGenerator:
    """
    Generate stunning 3D geospatial visualizations using PyDeck.
    Supports warehouse locations, supply chain routes, and demand heat maps.
    """
    
    def __init__(self, map_style: str = "mapbox://styles/mapbox/dark-v10"):
        """
        Initialize map generator.
        
        Args:
            map_style: Mapbox style URL
        """
        self.map_style = map_style
        self.default_view_state = pdk.ViewState(
            latitude=40.7128,
            longitude=-74.0060,
            zoom=10,
            pitch=45,
            bearing=0
        )
    
    def create_warehouse_locations_layer(
        self, 
        locations: List[WarehouseLocation],
        extruded: bool = True
    ) -> pdk.Layer:
        """
        Create 3D column layer for warehouse locations.
        Height represents utilization level.
        
        Args:
            locations: List of warehouse locations
            extruded: Whether to show 3D columns
            
        Returns:
            PyDeck Layer
        """
        data = []
        for loc in locations:
            data.append({
                "id": loc.id,
                "name": loc.name,
                "coordinates": [loc.coordinate.longitude, loc.coordinate.latitude],
                "utilization": loc.current_utilization,
                "elevation": loc.elevation_meters,
                "capacity": loc.capacity,
                "color": self._hex_to_rgb(loc.utilization_color),
                "facility_type": loc.facility_type.value
            })
        
        df = pd.DataFrame(data)
        
        return pdk.Layer(
            "ColumnLayer",
            data=df,
            get_position="coordinates",
            get_elevation="elevation",
            elevation_scale=100,
            radius=200,
            get_fill_color="color",
            pickable=True,
            extruded=extruded,
            auto_highlight=True,
            wireframe=True
        )
    
    def create_scatterplot_layer(
        self,
        locations: List[WarehouseLocation],
        radius_scale: float = 100
    ) -> pdk.Layer:
        """
        Create 2D scatterplot layer for warehouse locations.
        
        Args:
            locations: List of warehouse locations
            radius_scale: Scale factor for point size
            
        Returns:
            PyDeck Layer
        """
        data = []
        for loc in locations:
            data.append({
                "id": loc.id,
                "name": loc.name,
                "coordinates": [loc.coordinate.longitude, loc.coordinate.latitude],
                "utilization": loc.current_utilization,
                "capacity": loc.capacity,
                "color": self._hex_to_rgb(loc.utilization_color) + [200],
                "radius": loc.capacity / 10000  # Scale by capacity
            })
        
        df = pd.DataFrame(data)
        
        return pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position="coordinates",
            get_radius="radius",
            radius_scale=radius_scale,
            get_fill_color="color",
            pickable=True,
            auto_highlight=True
        )
    
    def create_routes_layer(
        self,
        routes: List[Route],
        arc_style: bool = True
    ) -> pdk.Layer:
        """
        Create layer showing supply chain routes.
        
        Args:
            routes: List of routes
            arc_style: If True, use ArcLayer (3D arcs), else PathLayer (2D lines)
            
        Returns:
            PyDeck Layer
        """
        data = []
        for route in routes:
            if not route.active:
                continue
                
            data.append({
                "id": route.id,
                "name": route.name or f"{route.origin.name} → {route.destination.name}",
                "source": [route.origin.coordinate.longitude, route.origin.coordinate.latitude],
                "target": [route.destination.coordinate.longitude, route.destination.coordinate.latitude],
                "distance": route.calculated_distance,
                "shipments": route.daily_shipments,
                "color": route.arc_color
            })
        
        df = pd.DataFrame(data)
        
        if arc_style:
            return pdk.Layer(
                "ArcLayer",
                data=df,
                get_source_position="source",
                get_target_position="target",
                get_source_color="color",
                get_target_color="color",
                get_width="shipments",
                width_scale=0.1,
                width_min_pixels=2,
                pickable=True,
                auto_highlight=True
            )
        else:
            # Convert to LineLayer format
            line_data = []
            for _, row in df.iterrows():
                line_data.append({
                    "path": [row["source"], row["target"]],
                    "name": row["name"],
                    "color": row["color"],
                    "width": max(row["shipments"] * 0.5, 2)
                })
            
            return pdk.Layer(
                "PathLayer",
                data=pd.DataFrame(line_data),
                get_path="path",
                get_color="color",
                get_width="width",
                width_min_pixels=2,
                pickable=True,
                auto_highlight=True
            )
    
    def create_demand_heatmap_layer(
        self,
        demand_points: List[DemandPoint],
        radius: int = 1000
    ) -> pdk.Layer:
        """
        Create hexagon heatmap showing demand distribution.
        
        Args:
            demand_points: List of demand points
            radius: Hexagon radius in meters
            
        Returns:
            PyDeck Layer
        """
        data = []
        for point in demand_points:
            data.append({
                "coordinates": [point.coordinate.longitude, point.coordinate.latitude],
                "demand": point.demand_volume,
                "category": point.product_category or "general"
            })
        
        df = pd.DataFrame(data)
        
        return pdk.Layer(
            "HexagonLayer",
            data=df,
            get_position="coordinates",
            get_elevation="demand",
            elevation_scale=50,
            elevation_range=[0, 3000],
            radius=radius,
            extruded=True,
            pickable=True,
            auto_highlight=True,
            coverage=0.8,
            color_range=[
                [65, 182, 196],
                [127, 205, 187],
                [199, 233, 180],
                [237, 248, 177],
                [255, 255, 204],
                [255, 237, 160],
                [254, 217, 118],
                [254, 178, 76],
                [253, 141, 60],
                [252, 78, 42],
                [227, 26, 28],
                [189, 0, 38],
            ]
        )
    
    def create_text_labels_layer(
        self,
        locations: List[WarehouseLocation]
    ) -> pdk.Layer:
        """
        Create text labels for warehouse locations.
        
        Args:
            locations: List of warehouse locations
            
        Returns:
            PyDeck Layer
        """
        data = []
        for loc in locations:
            data.append({
                "coordinates": [loc.coordinate.longitude, loc.coordinate.latitude],
                "text": loc.name,
                "size": 16,
                "color": [255, 255, 255, 255]
            })
        
        df = pd.DataFrame(data)
        
        return pdk.Layer(
            "TextLayer",
            data=df,
            get_position="coordinates",
            get_text="text",
            get_size="size",
            get_color="color",
            get_angle=0,
            get_text_anchor='"middle"',
            get_alignment_baseline='"center"',
            pickable=False
        )
    
    def create_supply_chain_map(
        self,
        network: SupplyChainNetwork,
        show_routes: bool = True,
        show_demand: bool = True,
        show_labels: bool = True,
        style: str = "3d"
    ) -> pdk.Deck:
        """
        Create complete supply chain visualization map.
        
        Args:
            network: Supply chain network
            show_routes: Whether to show routes
            show_demand: Whether to show demand heatmap
            show_labels: Whether to show location labels
            style: "3d" for columns or "2d" for scatterplot
            
        Returns:
            PyDeck Deck object ready to render
        """
        layers = []
        
        # Warehouse locations
        if style == "3d":
            layers.append(self.create_warehouse_locations_layer(network.facilities))
        else:
            layers.append(self.create_scatterplot_layer(network.facilities))
        
        # Routes
        if show_routes and network.routes:
            layers.append(self.create_routes_layer(network.routes, arc_style=(style == "3d")))
        
        # Demand heatmap
        if show_demand and network.demand_points:
            layers.append(self.create_demand_heatmap_layer(network.demand_points))
        
        # Labels
        if show_labels:
            layers.append(self.create_text_labels_layer(network.facilities))
        
        # Set view state based on network bounds
        view_state = self._calculate_view_state(network)
        
        # Create deck
        tooltip = {
            "html": "<b>{name}</b><br/>"
                    "Utilization: {utilization}%<br/>"
                    "Capacity: {capacity} m³<br/>"
                    "Type: {facility_type}",
            "style": {
                "backgroundColor": "steelblue",
                "color": "white",
                "fontSize": "12px",
                "padding": "8px"
            }
        }
        
        return pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            map_style=self.map_style,
            tooltip=tooltip
        )
    
    def create_simple_warehouse_map(
        self,
        locations: List[WarehouseLocation],
        center: Optional[GeoCoordinate] = None,
        zoom: int = 10
    ) -> pdk.Deck:
        """
        Create simple warehouse location map.
        
        Args:
            locations: List of warehouse locations
            center: Center coordinate (auto-calculated if None)
            zoom: Initial zoom level
            
        Returns:
            PyDeck Deck object
        """
        # Calculate center if not provided
        if center is None and locations:
            avg_lat = sum(loc.coordinate.latitude for loc in locations) / len(locations)
            avg_lon = sum(loc.coordinate.longitude for loc in locations) / len(locations)
            center = GeoCoordinate(latitude=avg_lat, longitude=avg_lon)
        
        view_state = pdk.ViewState(
            latitude=center.latitude if center else 0,
            longitude=center.longitude if center else 0,
            zoom=zoom,
            pitch=45,
            bearing=0
        )
        
        layer = self.create_warehouse_locations_layer(locations)
        
        return pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style=self.map_style
        )
    
    def _calculate_view_state(self, network: SupplyChainNetwork) -> pdk.ViewState:
        """Calculate optimal view state for network"""
        if not network.facilities:
            return self.default_view_state
        
        center = network.center_coordinate
        if not center:
            return self.default_view_state
        
        # Calculate zoom based on bounds
        if network.min_lat and network.max_lat and network.min_lon and network.max_lon:
            lat_range = network.max_lat - network.min_lat
            lon_range = network.max_lon - network.min_lon
            max_range = max(lat_range, lon_range)
            
            # Rough zoom calculation
            zoom = int(8 - np.log2(max_range + 1))
            zoom = max(3, min(zoom, 15))  # Clamp between 3 and 15
        else:
            zoom = 10
        
        return pdk.ViewState(
            latitude=center.latitude,
            longitude=center.longitude,
            zoom=zoom,
            pitch=45,
            bearing=0
        )
    
    @staticmethod
    def _hex_to_rgb(hex_color: str) -> List[int]:
        """Convert hex color to RGB list"""
        hex_color = hex_color.lstrip('#')
        return list(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def generate_sample_network(
    num_warehouses: int = 10,
    num_routes: int = 15,
    num_demand_points: int = 100,
    center_lat: float = 40.7128,
    center_lon: float = -74.0060,
    radius_km: float = 50
) -> SupplyChainNetwork:
    """
    Generate sample supply chain network for demonstration.
    
    Args:
        num_warehouses: Number of warehouse facilities
        num_routes: Number of routes
        num_demand_points: Number of demand points
        center_lat: Center latitude
        center_lon: Center longitude
        radius_km: Radius for random placement in km
        
    Returns:
        SupplyChainNetwork with sample data
    """
    facilities = []
    
    # Generate warehouses
    for i in range(num_warehouses):
        # Random offset within radius
        angle = np.random.uniform(0, 2 * np.pi)
        distance = np.random.uniform(0, radius_km)
        
        # Approximate lat/lon offset (1 degree ≈ 111 km)
        lat_offset = (distance * np.cos(angle)) / 111
        lon_offset = (distance * np.sin(angle)) / (111 * np.cos(np.radians(center_lat)))
        
        facility = WarehouseLocation(
            id=f"WH{i:03d}",
            name=f"Warehouse {i+1}",
            facility_type=FacilityType.WAREHOUSE if i % 3 != 0 else FacilityType.DISTRIBUTION_CENTER,
            coordinate=GeoCoordinate(
                latitude=center_lat + lat_offset,
                longitude=center_lon + lon_offset,
                elevation=np.random.uniform(0, 100)
            ),
            capacity=np.random.uniform(10000, 100000),
            current_utilization=np.random.uniform(30, 95),
            daily_throughput=np.random.randint(100, 5000),
            city=f"City {i+1}"
        )
        facilities.append(facility)
    
    # Generate routes
    routes = []
    for i in range(num_routes):
        if len(facilities) >= 2:
            origin, destination = np.random.choice(facilities, 2, replace=False)
            
            route = Route(
                id=f"ROUTE{i:03d}",
                name=f"Route {i+1}",
                origin=origin,
                destination=destination,
                daily_shipments=np.random.randint(10, 200),
                avg_load_kg=np.random.uniform(500, 5000),
                cost_per_km=np.random.uniform(0.5, 2.0),
                transport_mode=np.random.choice(["truck", "rail", "air"])
            )
            routes.append(route)
    
    # Generate demand points
    demand_points = []
    for i in range(num_demand_points):
        angle = np.random.uniform(0, 2 * np.pi)
        distance = np.random.uniform(0, radius_km * 1.2)
        
        lat_offset = (distance * np.cos(angle)) / 111
        lon_offset = (distance * np.sin(angle)) / (111 * np.cos(np.radians(center_lat)))
        
        demand = DemandPoint(
            id=f"DEM{i:03d}",
            coordinate=GeoCoordinate(
                latitude=center_lat + lat_offset,
                longitude=center_lon + lon_offset
            ),
            demand_volume=np.random.uniform(10, 1000),
            product_category=np.random.choice(["electronics", "groceries", "apparel", "pharma"])
        )
        demand_points.append(demand)
    
    network = SupplyChainNetwork(
        name="Sample Supply Chain Network",
        facilities=facilities,
        routes=routes,
        demand_points=demand_points
    )
    
    network.update_bounds()
    
    return network
