"""
Detailed Rack Visualization

Creates zoomed-in views of individual racks showing shelf-level details.
"""

import plotly.graph_objects as go
from typing import List, Optional
import numpy as np

from models.warehouse import WarehouseConfig, Product, RackSystem, Position3D


class RackDetailVisualizer:
    """
    Create detailed visualizations of individual racks.
    
    Features:
    - Zoomed-in view of single rack
    - All shelves with exact positions
    - Utilization per shelf
    - Zone color coding
    - Interactive product details
    """
    
    def __init__(self, warehouse_config: WarehouseConfig):
        """
        Initialize rack visualizer.
        
        Args:
            warehouse_config: Warehouse configuration
        """
        self.warehouse = warehouse_config
        
        # Zone colors
        self.zone_colors = {
            "A": "#4caf50",  # Green
            "B": "#2196f3",  # Blue
            "C": "#ff9800",  # Orange
            "D": "#f44336",  # Red
        }
    
    def visualize_rack(
        self,
        rack_id: str,
        products: Optional[List[Product]] = None
    ) -> go.Figure:
        """
        Create detailed visualization of a single rack.
        
        Args:
            rack_id: Rack identifier
            products: Products stored in this rack
            
        Returns:
            Plotly Figure
        """
        # Find rack in warehouse
        rack = self._find_rack(rack_id)
        if not rack:
            raise ValueError(f"Rack {rack_id} not found in warehouse")
        
        # Create figure
        fig = go.Figure()
        
        # Add rack structure
        self._add_rack_structure(fig, rack)
        
        # Add shelves
        self._add_shelves(fig, rack)
        
        # Add products if provided
        if products:
            rack_products = [p for p in products if p.rack_id == rack_id]
            self._add_products(fig, rack, rack_products)
        
        # Update layout
        fig.update_layout(
            title=f"Rack Detail View: {rack_id}",
            scene=dict(
                xaxis_title="Width (m)",
                yaxis_title="Depth (m)",
                zaxis_title="Height (m)",
                aspectmode='data',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            width=900,
            height=700,
            showlegend=True,
            hovermode='closest'
        )
        
        return fig
    
    def visualize_aisle(
        self,
        aisle_num: int,
        products: Optional[List[Product]] = None
    ) -> go.Figure:
        """
        Create visualization of entire aisle with multiple racks.
        
        Args:
            aisle_num: Aisle number
            products: Products in this aisle
            
        Returns:
            Plotly Figure
        """
        fig = go.Figure()
        
        # Find racks in this aisle
        aisle_racks = [
            rack for rack in self.warehouse.storage_systems
            if f"A{aisle_num}" in rack.id
        ]
        
        if not aisle_racks:
            raise ValueError(f"No racks found in aisle {aisle_num}")
        
        # Add each rack
        for rack in aisle_racks:
            self._add_rack_structure(fig, rack, opacity=0.3)
            self._add_shelves(fig, rack)
        
        # Add products
        if products:
            aisle_products = [
                p for p in products
                if any(rack.id == p.rack_id for rack in aisle_racks)
            ]
            for rack in aisle_racks:
                rack_products = [p for p in aisle_products if p.rack_id == rack.id]
                self._add_products(fig, rack, rack_products)
        
        # Update layout
        fig.update_layout(
            title=f"Aisle {aisle_num} Detail View",
            scene=dict(
                xaxis_title="Width (m)",
                yaxis_title="Depth (m)",
                zaxis_title="Height (m)",
                aspectmode='data'
            ),
            width=1200,
            height=700
        )
        
        return fig
    
    def _find_rack(self, rack_id: str) -> Optional[RackSystem]:
        """Find rack by ID"""
        for rack in self.warehouse.storage_systems:
            if rack.id == rack_id:
                return rack
        return None
    
    def _add_rack_structure(
        self, fig: go.Figure, rack: RackSystem, opacity: float = 0.2
    ):
        """Add rack frame structure"""
        pos = rack.position
        dims = rack.dimensions
        
        # Rack frame (vertical posts)
        posts = [
            # Front left
            ([pos.x, pos.x], [pos.y, pos.y], [pos.z, pos.z + dims.height]),
            # Front right
            ([pos.x + dims.width, pos.x + dims.width], [pos.y, pos.y],
             [pos.z, pos.z + dims.height]),
            # Back left
            ([pos.x, pos.x], [pos.y + dims.depth, pos.y + dims.depth],
             [pos.z, pos.z + dims.height]),
            # Back right
            ([pos.x + dims.width, pos.x + dims.width],
             [pos.y + dims.depth, pos.y + dims.depth],
             [pos.z, pos.z + dims.height]),
        ]
        
        for x, y, z in posts:
            fig.add_trace(go.Scatter3d(
                x=x, y=y, z=z,
                mode='lines',
                line=dict(color='gray', width=4),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Horizontal beams at each level
        zone_color = self.zone_colors.get(str(rack.zone), 'gray')
        
        for level in rack.levels:
            height = pos.z + level.height_from_floor
            
            # Front beam
            fig.add_trace(go.Scatter3d(
                x=[pos.x, pos.x + dims.width],
                y=[pos.y, pos.y],
                z=[height, height],
                mode='lines',
                line=dict(color=zone_color, width=3),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Back beam
            fig.add_trace(go.Scatter3d(
                x=[pos.x, pos.x + dims.width],
                y=[pos.y + dims.depth, pos.y + dims.depth],
                z=[height, height],
                mode='lines',
                line=dict(color=zone_color, width=3),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    def _add_shelves(self, fig: go.Figure, rack: RackSystem):
        """Add shelf markers"""
        pos = rack.position
        dims = rack.dimensions
        zone_color = self.zone_colors.get(str(rack.zone), 'gray')
        
        for level in rack.levels:
            height = pos.z + level.height_from_floor
            
            for shelf in level.shelves:
                # Calculate shelf position within rack
                shelf_x = pos.x + (shelf.position_in_rack / len(level.shelves)) * dims.width
                shelf_y = pos.y + dims.depth / 2
                
                # Shelf marker
                marker_size = 8 if shelf.occupied else 5
                marker_color = zone_color if shelf.occupied else 'lightgray'
                
                fig.add_trace(go.Scatter3d(
                    x=[shelf_x],
                    y=[shelf_y],
                    z=[height],
                    mode='markers',
                    marker=dict(
                        size=marker_size,
                        color=marker_color,
                        symbol='square',
                        opacity=0.8 if shelf.occupied else 0.3
                    ),
                    name=shelf.id,
                    hovertemplate=(
                        f"<b>Shelf: {shelf.id}</b><br>" +
                        f"Level: {level.level_number}<br>" +
                        f"Position: {shelf.position_in_rack}<br>" +
                        f"Occupied: {shelf.occupied}<br>" +
                        f"Load: {shelf.load_kg:.1f} kg / {shelf.max_load_kg} kg<br>" +
                        f"Utilization: {shelf.utilization_percent:.1f}%<br>" +
                        "<extra></extra>"
                    )
                ))
    
    def _add_products(
        self, fig: go.Figure, rack: RackSystem, products: List[Product]
    ):
        """Add product markers"""
        for product in products:
            if not product.position:
                continue
            
            zone_color = self.zone_colors.get(
                str(product.final_zone or product.predicted_zone), 'gray'
            )
            
            fig.add_trace(go.Scatter3d(
                x=[product.position.x],
                y=[product.position.y],
                z=[product.position.z],
                mode='markers+text',
                marker=dict(
                    size=10,
                    color=zone_color,
                    symbol='diamond',
                    line=dict(color='white', width=1)
                ),
                text=product.item_id,
                textposition='top center',
                textfont=dict(size=8),
                name=product.item_id,
                hovertemplate=(
                    f"<b>{product.item_id}</b><br>" +
                    f"Category: {product.category}<br>" +
                    f"Zone: {product.final_zone or product.predicted_zone}<br>" +
                    f"Shelf: {product.shelf}<br>" +
                    f"Stock: {product.stock_level} units<br>" +
                    f"Daily Demand: {product.daily_demand}<br>" +
                    "<extra></extra>"
                )
            ))
