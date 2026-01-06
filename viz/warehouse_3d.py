"""
Warehouse 3D Visualization Module

Creates interactive 3D visualizations of warehouse layouts with products,
racks, aisles, and entry/exit paths.
"""

import plotly.graph_objects as go
import numpy as np
from typing import List, Optional, Tuple
from models.warehouse import WarehouseConfig, Product, ZoneType, Position3D


class Warehouse3DVisualizer:
    """
    Create interactive 3D warehouse visualizations with Plotly.
    
    Features:
    - Warehouse structure (walls, floor, ceiling, aisles, racks)
    - Product placement with zone-based colors
    - Entry and exit path highlighting
    - Adaptive sizing based on warehouse dimensions
    """
    
    def __init__(self, warehouse_config: WarehouseConfig):
        """
        Initialize visualizer with warehouse configuration.
        
        Args:
            warehouse_config: Warehouse configuration model
        """
        self.config = warehouse_config
        self.warehouse_length = warehouse_config.warehouse_length
        self.warehouse_width = warehouse_config.dimensions.width
        self.warehouse_height = warehouse_config.dimensions.height
        
        # Zone colors for product visualization
        self.zone_colors = {
            "A": "#4caf50",  # Green - high-value
            "B": "#2196f3",  # Blue - medium-value
            "C": "#ff9800",  # Orange - bulky items
            "D": "#f44336",  # Red - long-term storage
        }
        
        # Entry/Exit positions (calculated based on warehouse layout)
        self.entry_position = self._calculate_entry_position()
        self.exit_position = self._calculate_exit_position()
    
    def _calculate_entry_position(self) -> Position3D:
        """
        Calculate optimal entry position based on warehouse layout.
        Typically at the front-left corner.
        """
        return Position3D(x=2.0, y=2.0, z=0.0)
    
    def _calculate_exit_position(self) -> Position3D:
        """
        Calculate optimal exit position based on warehouse layout.
        Typically at the front-right corner.
        """
        return Position3D(x=self.warehouse_width - 2.0, y=2.0, z=0.0)
    
    def create_visualization(
        self,
        products: Optional[List[Product]] = None,
        show_products: bool = True,
        max_products_display: int = 1000,
        show_entry_exit: bool = True
    ) -> go.Figure:
        """
        Create complete 3D warehouse visualization.
        
        Args:
            products: List of products to display
            show_products: Whether to show products
            max_products_display: Maximum number of products to display
            show_entry_exit: Whether to show entry/exit paths
            
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        # Add warehouse structure
        self._add_warehouse_structure(fig)
        
        # Add racks/aisles
        self._add_racks_and_aisles(fig)
        
        # Add entry/exit paths
        if show_entry_exit:
            self._add_entry_exit_paths(fig)
        
        # Add products if provided
        if show_products and products:
            self._add_products(fig, products, max_products_display)
        
        # Configure layout
        self._configure_layout(fig)
        
        return fig
    
    def _add_warehouse_structure(self, fig: go.Figure):
        """Add warehouse walls, floor, and ceiling."""
        # Floor
        fig.add_trace(go.Mesh3d(
            x=[0, self.warehouse_width, self.warehouse_width, 0],
            y=[0, 0, self.warehouse_length, self.warehouse_length],
            z=[0, 0, 0, 0],
            i=[0, 0],
            j=[1, 2],
            k=[2, 3],
            color='lightgray',
            opacity=0.2,
            name='Floor',
            showlegend=True,
            hoverinfo='name'
        ))
        
        # Walls outline (using scatter3d for edges)
        # Front wall
        fig.add_trace(go.Scatter3d(
            x=[0, self.warehouse_width, self.warehouse_width, 0, 0],
            y=[0, 0, 0, 0, 0],
            z=[0, 0, self.warehouse_height, self.warehouse_height, 0],
            mode='lines',
            line=dict(color='gray', width=2),
            name='Walls',
            showlegend=True,
            hoverinfo='name'
        ))
        
        # Back wall
        fig.add_trace(go.Scatter3d(
            x=[0, self.warehouse_width, self.warehouse_width, 0, 0],
            y=[self.warehouse_length, self.warehouse_length, self.warehouse_length, self.warehouse_length, self.warehouse_length],
            z=[0, 0, self.warehouse_height, self.warehouse_height, 0],
            mode='lines',
            line=dict(color='gray', width=2),
            name='Walls',
            showlegend=False,
            hoverinfo='name'
        ))
        
        # Side edges
        for x_pos in [0, self.warehouse_width]:
            fig.add_trace(go.Scatter3d(
                x=[x_pos, x_pos],
                y=[0, self.warehouse_length],
                z=[0, 0],
                mode='lines',
                line=dict(color='gray', width=2),
                name='Walls',
                showlegend=False,
                hoverinfo='name'
            ))
            fig.add_trace(go.Scatter3d(
                x=[x_pos, x_pos],
                y=[0, self.warehouse_length],
                z=[self.warehouse_height, self.warehouse_height],
                mode='lines',
                line=dict(color='gray', width=2),
                name='Walls',
                showlegend=False,
                hoverinfo='name'
            ))
    
    def _add_racks_and_aisles(self, fig: go.Figure):
        """Add rack structures and aisles to the visualization."""
        num_aisles = self.config.layout.num_aisles
        aisle_width = self.config.layout.aisle_width
        
        # Determine how many aisles to visualize (sample for large warehouses)
        aisles_to_show = min(num_aisles, 20) if num_aisles > 50 else num_aisles
        
        # Calculate aisle positions
        total_width = self.warehouse_width
        aisle_spacing = total_width / (aisles_to_show + 1)
        
        for i in range(aisles_to_show):
            x_pos = (i + 1) * aisle_spacing
            
            # Add aisle marker (center line)
            fig.add_trace(go.Scatter3d(
                x=[x_pos, x_pos],
                y=[0, self.warehouse_length],
                z=[0, 0],
                mode='lines',
                line=dict(color='yellow', width=1, dash='dash'),
                name=f'Aisle {i+1}' if i == 0 else '',
                showlegend=(i == 0),
                hoverinfo='name'
            ))
            
            # Add rack representations on both sides of aisle
            rack_height = min(self.warehouse_height * 0.8, 8.0)
            rack_depth = self.config.layout.rack_depth
            
            # Left rack
            if x_pos - aisle_width/2 > 0:
                self._add_rack_representation(
                    fig,
                    x_pos - aisle_width/2 - rack_depth/2,
                    0,
                    self.warehouse_length,
                    rack_depth,
                    rack_height,
                    show_legend=(i == 0)
                )
            
            # Right rack
            if x_pos + aisle_width/2 < total_width:
                self._add_rack_representation(
                    fig,
                    x_pos + aisle_width/2 + rack_depth/2,
                    0,
                    self.warehouse_length,
                    rack_depth,
                    rack_height,
                    show_legend=False
                )
    
    def _add_rack_representation(
        self,
        fig: go.Figure,
        x_center: float,
        y_start: float,
        y_end: float,
        depth: float,
        height: float,
        show_legend: bool = False
    ):
        """Add a simplified rack representation."""
        # Rack as a vertical plane
        x_left = x_center - depth/2
        x_right = x_center + depth/2
        
        # Draw vertical posts at intervals
        num_posts = max(3, int((y_end - y_start) / 5))
        y_positions = np.linspace(y_start, y_end, num_posts)
        
        for y_pos in y_positions:
            fig.add_trace(go.Scatter3d(
                x=[x_center, x_center],
                y=[y_pos, y_pos],
                z=[0, height],
                mode='lines',
                line=dict(color='darkgray', width=3),
                name='Racks' if show_legend else '',
                showlegend=show_legend,
                hoverinfo='name'
            ))
            show_legend = False
    
    def _add_entry_exit_paths(self, fig: go.Figure):
        """Add entry and exit path markers."""
        # Entry path (green)
        entry = self.entry_position
        fig.add_trace(go.Scatter3d(
            x=[entry.x],
            y=[entry.y],
            z=[entry.z + 0.5],
            mode='markers+text',
            marker=dict(
                symbol='diamond',  # Valid Plotly symbol
                size=15,
                color='green',
                line=dict(color='darkgreen', width=2)
            ),
            text=['ENTRY'],
            textposition='top center',
            textfont=dict(size=12, color='green', family='Arial Black'),
            name='Entry Path',
            showlegend=True,
            hoverinfo='name'
        ))
        
        # Exit path (red)
        exit_pos = self.exit_position
        fig.add_trace(go.Scatter3d(
            x=[exit_pos.x],
            y=[exit_pos.y],
            z=[exit_pos.z + 0.5],
            mode='markers+text',
            marker=dict(
                symbol='diamond',  # Valid Plotly symbol
                size=15,
                color='red',
                line=dict(color='darkred', width=2)
            ),
            text=['EXIT'],
            textposition='top center',
            textfont=dict(size=12, color='red', family='Arial Black'),
            name='Exit Path',
            showlegend=True,
            hoverinfo='name'
        ))
        
        # Draw path lines from entry to main warehouse area
        center_y = self.warehouse_length / 2
        fig.add_trace(go.Scatter3d(
            x=[entry.x, entry.x],
            y=[entry.y, center_y],
            z=[0.1, 0.1],
            mode='lines',
            line=dict(color='green', width=4, dash='dot'),
            name='Entry Path',
            showlegend=False,
            hoverinfo='name'
        ))
        
        # Draw path lines from exit to main warehouse area
        fig.add_trace(go.Scatter3d(
            x=[exit_pos.x, exit_pos.x],
            y=[exit_pos.y, center_y],
            z=[0.1, 0.1],
            mode='lines',
            line=dict(color='red', width=4, dash='dot'),
            name='Exit Path',
            showlegend=False,
            hoverinfo='name'
        ))
    
    def _add_products(
        self,
        fig: go.Figure,
        products: List[Product],
        max_display: int
    ):
        """
        Add product markers to the visualization.
        
        Uses valid Plotly Scatter3d symbols: 'circle', 'square', 'diamond', etc.
        """
        # Sample products if too many
        display_products = products[:max_display] if len(products) > max_display else products
        
        # Group products by zone
        products_by_zone = {}
        unallocated_products = []
        
        for product in display_products:
            zone = product.final_zone or product.predicted_zone
            if zone:
                zone_key = zone.value if hasattr(zone, 'value') else str(zone)
                if zone_key not in products_by_zone:
                    products_by_zone[zone_key] = []
                products_by_zone[zone_key].append(product)
            else:
                # Products without zone assignment
                unallocated_products.append(product)
        
        # Add unallocated products to a default zone if any exist
        if unallocated_products:
            products_by_zone['UNALLOCATED'] = unallocated_products
        
        # Add products for each zone
        for zone, zone_products in products_by_zone.items():
            # Generate positions if not already assigned
            positions = self._generate_product_positions(zone_products, zone)
            
            x_coords = [p[0] for p in positions]
            y_coords = [p[1] for p in positions]
            z_coords = [p[2] for p in positions]
            
            # Get zone color
            color = self.zone_colors.get(zone, '#9e9e9e')
            
            # Use valid Plotly symbols - 'square' is valid for Scatter3d
            fig.add_trace(go.Scatter3d(
                x=x_coords,
                y=y_coords,
                z=z_coords,
                mode='markers',
                marker=dict(
                    symbol='square',  # Valid symbol: square, circle, diamond, cross, x
                    size=4,
                    color=color,
                    opacity=0.7,
                    line=dict(color='white', width=0.5)
                ),
                name=f'Products Zone {zone}',
                text=[f"{p.item_id}<br>Zone: {zone}<br>Category: {p.category}" 
                      for p in zone_products],
                hoverinfo='text',
                showlegend=True
            ))
    
    def _generate_product_positions(
        self,
        products: List[Product],
        zone: str
    ) -> List[Tuple[float, float, float]]:
        """
        Generate 3D positions for products based on zone and warehouse layout.
        
        This method optimizes product placement considering:
        - Distance from entry/exit paths
        - Zone allocation
        - Product characteristics
        """
        positions = []
        
        # Zone-based positioning
        # Zone A: Near entry (high turnover)
        # Zone B: Middle area
        # Zone C: Deep storage (bulky)
        # Zone D: Far back (low turnover)
        # UNALLOCATED: Random placement
        
        zone_ranges = {
            "A": (0.1, 0.3),  # Front 10-30%
            "B": (0.3, 0.6),  # Middle 30-60%
            "C": (0.6, 0.8),  # Back-middle 60-80%
            "D": (0.8, 0.95), # Far back 80-95%
            "UNALLOCATED": (0.1, 0.95)  # Anywhere
        }
        
        y_range = zone_ranges.get(zone, (0.2, 0.8))
        y_min = self.warehouse_length * y_range[0]
        y_max = self.warehouse_length * y_range[1]
        
        for i, product in enumerate(products):
            # Check if product has assigned position
            if product.position:
                positions.append((
                    product.position.x,
                    product.position.y,
                    product.position.z
                ))
            else:
                # Generate random position within zone range
                x = np.random.uniform(2, self.warehouse_width - 2)
                y = np.random.uniform(y_min, y_max)
                z = np.random.uniform(0.5, min(self.warehouse_height * 0.8, 6.0))
                
                positions.append((x, y, z))
        
        return positions
    
    def _configure_layout(self, fig: go.Figure):
        """Configure the 3D plot layout."""
        fig.update_layout(
            title=dict(
                text=f"🏭 {self.config.name} - 3D Warehouse Layout<br>"
                     f"<sub>Dimensions: {self.warehouse_length:.0f}m × "
                     f"{self.warehouse_width:.0f}m × {self.warehouse_height:.0f}m | "
                     f"Aisles: {self.config.layout.num_aisles}</sub>",
                x=0.5,
                xanchor='center',
                font=dict(size=16)
            ),
            scene=dict(
                xaxis=dict(
                    title='Width (m)',
                    backgroundcolor='white',
                    gridcolor='lightgray',
                    showbackground=True,
                    range=[0, self.warehouse_width]
                ),
                yaxis=dict(
                    title='Length (m)',
                    backgroundcolor='white',
                    gridcolor='lightgray',
                    showbackground=True,
                    range=[0, self.warehouse_length]
                ),
                zaxis=dict(
                    title='Height (m)',
                    backgroundcolor='white',
                    gridcolor='lightgray',
                    showbackground=True,
                    range=[0, self.warehouse_height]
                ),
                aspectmode='data',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.2),
                    center=dict(x=0, y=0, z=0)
                )
            ),
            showlegend=True,
            legend=dict(
                x=1.02,
                y=1,
                xanchor='left',
                yanchor='top',
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='gray',
                borderwidth=1
            ),
            margin=dict(l=0, r=0, t=80, b=0),
            height=700,
            hovermode='closest'
        )
