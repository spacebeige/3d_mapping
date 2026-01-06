"""
3D Warehouse Visualization using Plotly

Creates detailed 3D warehouse models with racks, aisles, products, and AGVs.
"""

from typing import List, Optional, Dict, Any, Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd

from models.warehouse import (
    WarehouseConfig,
    RackSystem,
    Aisle,
    Product,
    Position3D,
    Dimensions3D,
    RackLevel,
    Shelf
)
from models.agv import AGV, PathNode


class Warehouse3DVisualizer:
    """
    Generate detailed 3D warehouse visualizations with realistic geometry.
    Optimized for large warehouses with 100,000+ shelves.
    """
    
    def __init__(self, config: WarehouseConfig):
        """
        Initialize visualizer.
        
        Args:
            config: Warehouse configuration
        """
        self.config = config
        self.fig: Optional[go.Figure] = None
        
        # Color schemes
        self.zone_colors = {
            "A": "#4caf50",  # Green - High value
            "B": "#2196f3",  # Blue - Medium value
            "C": "#ff9800",  # Orange - Bulky
            "D": "#f44336",  # Red - Low demand
        }
        
        self.material_colors = {
            "floor": "lightgray",
            "rack_frame": "#455a64",  # Dark gray
            "rack_beam": "#78909c",  # Light gray
            "pallet": "#8d6e63",  # Brown
            "wall": "#cfd8dc",  # Light blue-gray
        }
    
    def create_visualization(
        self,
        products: Optional[List[Product]] = None,
        agvs: Optional[List[AGV]] = None,
        show_products: bool = True,
        show_agvs: bool = True,
        show_grid: bool = False,
        max_products_display: int = 1000
    ) -> go.Figure:
        """
        Create complete 3D warehouse visualization.
        
        Args:
            products: Products to display
            agvs: AGVs to display
            show_products: Whether to show individual products
            show_agvs: Whether to show AGVs
            show_grid: Whether to show navigation grid
            max_products_display: Maximum products to display (for performance)
            
        Returns:
            Plotly Figure object
        """
        self.fig = go.Figure()
        
        # Add warehouse structure
        self._add_floor()
        self._add_walls()
        self._add_racks_detailed()
        self._add_aisles()
        
        # Add products if provided
        if show_products and products:
            self._add_products(products, max_display=max_products_display)
        
        # Add AGVs if provided
        if show_agvs and agvs:
            self._add_agvs(agvs)
        
        # Add navigation grid
        if show_grid:
            self._add_navigation_grid()
        
        # Update layout
        self._configure_layout()
        
        return self.fig
    
    def _add_floor(self):
        """Add warehouse floor"""
        width = self.config.dimensions.width
        length = self.config.dimensions.length or self.config.dimensions.depth
        
        self.fig.add_trace(go.Mesh3d(
            x=[0, width, width, 0],
            y=[0, 0, length, length],
            z=[0, 0, 0, 0],
            color=self.material_colors["floor"],
            opacity=0.9,
            name='Floor',
            showlegend=True,
            hoverinfo='skip'
        ))
    
    def _add_walls(self):
        """Add warehouse walls (optional, for context)"""
        width = self.config.dimensions.width
        length = self.config.dimensions.length or self.config.dimensions.depth
        height = self.config.dimensions.height
        
        # Front wall
        self.fig.add_trace(go.Mesh3d(
            x=[0, width, width, 0, 0, width, width, 0],
            y=[0, 0, 0, 0, 0, 0, 0, 0],
            z=[0, 0, height, height, 0, 0, height, height],
            i=[0, 0, 0, 1, 4, 4],
            j=[1, 2, 4, 2, 5, 6],
            k=[2, 3, 5, 6, 6, 7],
            color=self.material_colors["wall"],
            opacity=0.2,
            name='Walls',
            showlegend=False,
            hoverinfo='skip'
        ))
    
    def _add_racks_detailed(self):
        """Add detailed rack structures with beams and levels"""
        for rack in self.config.storage_systems:
            self._add_single_rack_detailed(rack)
    
    def _add_single_rack_detailed(self, rack: RackSystem):
        """
        Add a single rack with detailed structure.
        
        Args:
            rack: Rack system to add
        """
        pos = rack.position
        dim = rack.dimensions
        
        # Rack frame (vertical posts)
        post_width = 0.1
        post_depth = 0.1
        
        # Four corner posts
        posts = [
            (pos.x, pos.y),
            (pos.x + dim.width - post_width, pos.y),
            (pos.x, pos.y + (dim.length or dim.depth) - post_depth),
            (pos.x + dim.width - post_width, pos.y + (dim.length or dim.depth) - post_depth)
        ]
        
        for px, py in posts:
            self.fig.add_trace(go.Mesh3d(
                x=[px, px + post_width, px + post_width, px],
                y=[py, py, py + post_depth, py + post_depth],
                z=[0, 0, 0, 0],
                color=self.material_colors["rack_frame"],
                opacity=0.9,
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Vertical extension
            self.fig.add_trace(go.Mesh3d(
                x=[px, px + post_width, px + post_width, px, px, px + post_width, px + post_width, px],
                y=[py, py, py + post_depth, py + post_depth, py, py, py + post_depth, py + post_depth],
                z=[0, 0, 0, 0, dim.height, dim.height, dim.height, dim.height],
                i=[0, 0, 0, 1, 4, 4],
                j=[1, 2, 4, 2, 5, 6],
                k=[2, 3, 5, 6, 6, 7],
                color=self.material_colors["rack_frame"],
                opacity=0.9,
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Horizontal beams at each level
        num_levels = len(rack.levels) if rack.levels else int(dim.height / 1.5)
        level_height = dim.height / (num_levels if num_levels > 0 else 1)
        
        for level_idx in range(num_levels + 1):
            z_pos = level_idx * level_height
            beam_thickness = 0.05
            
            # Front and back beams
            for y_offset in [0, (dim.length or dim.depth)]:
                self.fig.add_trace(go.Scatter3d(
                    x=[pos.x, pos.x + dim.width],
                    y=[pos.y + y_offset, pos.y + y_offset],
                    z=[z_pos, z_pos],
                    mode='lines',
                    line=dict(color=self.material_colors["rack_beam"], width=3),
                    showlegend=False,
                    hoverinfo='skip'
                ))
        
        # Add zone color indicator
        if rack.zone:
            zone_color = self.zone_colors.get(rack.zone.value, "gray")
            # Zone marker at top of rack
            marker_height = dim.height + 0.5
            self.fig.add_trace(go.Scatter3d(
                x=[pos.x + dim.width / 2],
                y=[pos.y + (dim.length or dim.depth) / 2],
                z=[marker_height],
                mode='markers',
                marker=dict(size=8, color=zone_color, symbol='diamond'),
                name=f'Zone {rack.zone.value}',
                showlegend=False,
                hovertext=f'Rack {rack.id} - Zone {rack.zone.value}',
                hoverinfo='text'
            ))
    
    def _add_aisles(self):
        """Add aisle visualization"""
        for aisle in self.config.layout.aisle_positions:
            length = self.config.dimensions.length or self.config.dimensions.depth
            
            # Aisle floor marking
            self.fig.add_trace(go.Mesh3d(
                x=[aisle.x_position, aisle.x_position + aisle.width,
                   aisle.x_position + aisle.width, aisle.x_position],
                y=[0, 0, length, length],
                z=[0.01, 0.01, 0.01, 0.01],  # Slightly above floor
                color='yellow' if aisle.accessible else 'red',
                opacity=0.3,
                name=f'Aisle {aisle.id}',
                showlegend=False,
                hovertext=f'{aisle.id} - {"Accessible" if aisle.accessible else "Blocked"}',
                hoverinfo='text'
            ))
    
    def _add_products(self, products: List[Product], max_display: int = 1000):
        """
        Add products to visualization.
        For large warehouses, samples products for performance.
        
        Args:
            products: List of products
            max_display: Maximum products to display
        """
        # Sample products if too many
        if len(products) > max_display:
            import random
            products = random.sample(products, max_display)
        
        # Group by zone for efficient rendering
        zone_products: Dict[str, List[Product]] = {}
        for product in products:
            if product.final_zone:
                zone = product.final_zone.value
                if zone not in zone_products:
                    zone_products[zone] = []
                zone_products[zone].append(product)
        
        # Add products by zone
        for zone, zone_prods in zone_products.items():
            positions = self._assign_product_positions(zone_prods, zone)
            
            x_coords = [p[0] for p in positions]
            y_coords = [p[1] for p in positions]
            z_coords = [p[2] for p in positions]
            
            zone_color = self.zone_colors.get(zone, "gray")
            
            self.fig.add_trace(go.Scatter3d(
                x=x_coords,
                y=y_coords,
                z=z_coords,
                mode='markers',
                marker=dict(
                    size=3,
                    color=zone_color,
                    opacity=0.7,
                    symbol='cube'
                ),
                name=f'Products Zone {zone}',
                text=[f'{p.item_id}: {p.description}' for p in zone_prods],
                hoverinfo='text'
            ))
    
    def _assign_product_positions(
        self,
        products: List[Product],
        zone: str
    ) -> List[Tuple[float, float, float]]:
        """
        Assign 3D positions to products within their zone.
        
        Args:
            products: Products to position
            zone: Zone identifier
            
        Returns:
            List of (x, y, z) positions
        """
        positions = []
        
        # Find racks in this zone
        zone_racks = [r for r in self.config.storage_systems if r.zone and r.zone.value == zone]
        
        if not zone_racks:
            # Fallback: random positions
            for _ in products:
                pos = (
                    np.random.uniform(0, self.config.dimensions.width),
                    np.random.uniform(0, self.config.dimensions.length or self.config.dimensions.depth),
                    np.random.uniform(0, self.config.dimensions.height * 0.8)
                )
                positions.append(pos)
        else:
            # Distribute across zone racks
            for i, product in enumerate(products):
                rack = zone_racks[i % len(zone_racks)]
                pos = rack.position
                dim = rack.dimensions
                
                # Random position within rack
                x = pos.x + np.random.uniform(0.2, dim.width - 0.2)
                y = pos.y + np.random.uniform(0.2, (dim.length or dim.depth) - 0.2)
                z = np.random.uniform(0.5, dim.height * 0.9)
                
                positions.append((x, y, z))
        
        return positions
    
    def _add_agvs(self, agvs: List[AGV]):
        """Add AGVs to visualization"""
        if not agvs:
            return
        
        x_coords = [agv.current_position.x for agv in agvs]
        y_coords = [agv.current_position.y for agv in agvs]
        z_coords = [agv.current_position.z for agv in agvs]
        colors = [agv.color_by_status for agv in agvs]
        
        self.fig.add_trace(go.Scatter3d(
            x=x_coords,
            y=y_coords,
            z=z_coords,
            mode='markers+text',
            marker=dict(
                size=8,
                color=colors,
                symbol='diamond',
                line=dict(color='black', width=1)
            ),
            text=[agv.name for agv in agvs],
            textposition='top center',
            name='AGVs',
            hovertext=[
                f'{agv.name}<br>Status: {agv.status.value}<br>Battery: {agv.battery_level}%<br>Load: {agv.load_percentage:.1f}%'
                for agv in agvs
            ],
            hoverinfo='text'
        ))
    
    def _add_navigation_grid(self):
        """Add navigation grid for AGV pathfinding"""
        # This would add nodes and edges for visualization
        # Simplified version for performance
        pass
    
    def _configure_layout(self):
        """Configure 3D plot layout"""
        width = self.config.dimensions.width
        length = self.config.dimensions.length or self.config.dimensions.depth
        height = self.config.dimensions.height
        
        # Calculate aspect ratio
        max_dim = max(width, length, height)
        aspect_x = width / max_dim
        aspect_y = length / max_dim
        aspect_z = height / max_dim
        
        self.fig.update_layout(
            title=dict(
                text=f"3D Warehouse: {self.config.name}<br>"
                     f"<sub>{width}m × {length}m × {height}m | "
                     f"{len(self.config.storage_systems)} racks | "
                     f"Utilization: {self.config.overall_utilization:.1f}%</sub>",
                x=0.5,
                xanchor='center'
            ),
            scene=dict(
                xaxis=dict(title='Width (m)', range=[0, width]),
                yaxis=dict(title='Length (m)', range=[0, length]),
                zaxis=dict(title='Height (m)', range=[0, height]),
                aspectmode='manual',
                aspectratio=dict(x=aspect_x, y=aspect_y, z=aspect_z),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.2),
                    center=dict(x=0, y=0, z=0)
                )
            ),
            width=1200,
            height=800,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            hovermode='closest'
        )
